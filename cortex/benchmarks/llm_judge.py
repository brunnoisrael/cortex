"""LLM Judge para avaliação semântica de respostas e evidências no Cortex Benchmark.

Quando uma API externa de LLM não está configurada, este módulo suporta o
protocolo Code-Agent-as-Judge via Skill de IDE (Antigravity/Claude Code):
1. O benchmark exporta um lote de julgamento (``judge_inbox.json``);
2. O Code Agent analisa o lote sob a rubrica da Skill e grava ``judge_verdicts.json``;
3. O módulo calcula métricas de suporte semântico, ranking e fidelidade.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from cortex.benchmarks.metrics import mrr as calc_mrr
from cortex.benchmarks.metrics import precision_at_k as calc_precision_at_k
from cortex.benchmarks.metrics import recall_at_k as calc_recall_at_k


@dataclass
class JudgeCase:
    case_id: str
    task_type: str
    query: str
    gold_answer: str | None
    accepted_answers: list[str]
    expected_abstention: bool
    gold_evidence: list[str]
    retrieved_evidence_ids: list[str]
    retrieved_evidence_texts: list[str]
    compiled_context: str
    abstained: bool
    missing_evidence: list[str]


@dataclass
class JudgeVerdict:
    case_id: str
    answer_supported: bool
    relevance_ranking: list[str] = field(default_factory=list)
    abstention_appropriate: bool = True
    fidelity_score: float = 1.0
    reasoning: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_judge_cases(
    instances: list[Any],
    results: list[Any],
) -> list[JudgeCase]:
    """Cria os casos do lote de julgamento correlacionando instância e resultado."""
    result_by_case = {r.case_id: r for r in results}
    cases: list[JudgeCase] = []

    for inst in instances:
        res = result_by_case.get(inst.id)
        if not res:
            continue

        evidence_texts: list[str] = []
        ev_ids_set = set(res.evidence or res.selected or [])
        for sess in inst.history_until_cutoff():
            for ev in sess.events:
                if ev.id in ev_ids_set:
                    evidence_texts.append(f"[{ev.id}] ({ev.role}) {ev.content}")

        compiled_ctx = ""
        if hasattr(res, "trace") and isinstance(res.trace, dict):
            compiled_ctx = res.trace.get("context", "")

        cases.append(JudgeCase(
            case_id=inst.id,
            task_type=inst.task_type,
            query=inst.query.text,
            gold_answer=inst.gold.answer,
            accepted_answers=list(inst.gold.accepted_answers or []),
            expected_abstention=bool(inst.gold.expected_abstention),
            gold_evidence=list(inst.gold.gold_evidence or []),
            retrieved_evidence_ids=list(res.evidence or res.selected or []),
            retrieved_evidence_texts=evidence_texts,
            compiled_context=compiled_ctx,
            abstained=bool(res.abstained),
            missing_evidence=list(res.missing_evidence or []),
        ))

    return cases


def export_judge_inbox(cases: list[JudgeCase], out_path: Path) -> Path:
    """Exporta o lote de julgamento para o formato consumível pelo Code Agent."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "benchmark_cases_count": len(cases),
        "protocol": "code_agent_as_judge/v1",
        "instructions": (
            "Para cada caso em 'cases', avalie: "
            "1. answer_supported: se os dados recuperados contêm o fato necessário para a resposta esperada; "
            "2. relevance_ranking: ordene os IDs de evidência por relevância para responder à pergunta; "
            "3. abstention_appropriate: se a decisão de se abster (ou responder) foi correta; "
            "4. fidelity_score: pontuação de 0.0 a 1.0; "
            "5. reasoning: justificativa técnica concisa."
        ),
        "cases": [asdict(c) for c in cases],
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out_path


def load_verdicts(verdicts_path: Path) -> dict[str, JudgeVerdict]:
    """Carrega os vereditos emitidos pelo Judge."""
    raw = json.loads(verdicts_path.read_text(encoding="utf-8"))
    entries = raw if isinstance(raw, list) else raw.get("verdicts", [])
    verdicts: dict[str, JudgeVerdict] = {}
    for item in entries:
        cid = item["case_id"]
        verdicts[cid] = JudgeVerdict(
            case_id=cid,
            answer_supported=bool(item.get("answer_supported", False)),
            relevance_ranking=list(item.get("relevance_ranking") or []),
            abstention_appropriate=bool(item.get("abstention_appropriate", True)),
            fidelity_score=float(item.get("fidelity_score", 1.0)),
            reasoning=str(item.get("reasoning", "")),
        )
    return verdicts


def evaluate_judge_metrics(
    cases: list[JudgeCase],
    verdicts: dict[str, JudgeVerdict],
) -> dict[str, Any]:
    """Calcula métricas avaliadas pelo LLM Judge."""
    answer_supports: list[float] = []
    mrrs: list[float] = []
    precisions_at_k: list[float] = []
    abstention_matches: list[float] = []
    fidelities: list[float] = []

    for c in cases:
        verd = verdicts.get(c.case_id)
        if not verd:
            continue

        abstention_matches.append(1.0 if verd.abstention_appropriate else 0.0)
        fidelities.append(verd.fidelity_score)

        if c.expected_abstention:
            continue

        answer_supports.append(1.0 if verd.answer_supported else 0.0)

        ranking = verd.relevance_ranking or c.retrieved_evidence_ids
        if c.gold_evidence:
            mrrs.append(calc_mrr(ranking, c.gold_evidence))
            precisions_at_k.append(calc_precision_at_k(ranking, c.gold_evidence, k=3))

    def _mean(vals: list[float]) -> float:
        return sum(vals) / len(vals) if vals else 0.0

    return {
        "cases_evaluated": len(verdicts),
        "total_cases": len(cases),
        "judge_answer_support_recall": round(_mean(answer_supports), 4),
        "judge_mrr": round(_mean(mrrs), 4),
        "judge_precision_at_k": round(_mean(precisions_at_k), 4),
        "judge_abstention_accuracy": round(_mean(abstention_matches), 4),
        "judge_mean_fidelity": round(_mean(fidelities), 4),
    }


def generate_heuristic_verdicts(cases: list[JudgeCase]) -> dict[str, JudgeVerdict]:
    """Fallback determinístico heurístico para ambientes automatizados."""
    from cortex.compiler.compiler import keyword_overlap

    verdicts: dict[str, JudgeVerdict] = {}
    for c in cases:
        if c.expected_abstention:
            verdicts[c.case_id] = JudgeVerdict(
                case_id=c.case_id,
                answer_supported=False,
                relevance_ranking=[],
                abstention_appropriate=c.abstained,
                fidelity_score=1.0 if c.abstained else 0.0,
                reasoning="Abstenção esperada e confirmada para tópico ausente.",
            )
            continue

        joined_ev = " ".join(c.retrieved_evidence_texts)
        gold_ans = c.gold_answer or ""
        supported = False
        if c.accepted_answers:
            supported = any(acc.lower() in joined_ev.lower() for acc in c.accepted_answers)
        if not supported and gold_ans:
            overlap = keyword_overlap(gold_ans, joined_ev)
            supported = overlap >= 0.25

        ranking = list(c.retrieved_evidence_ids)
        ranking.sort(
            key=lambda eid: -keyword_overlap(c.query, next((t for t in c.retrieved_evidence_texts if eid in t), ""))
        )

        verdicts[c.case_id] = JudgeVerdict(
            case_id=c.case_id,
            answer_supported=supported,
            relevance_ranking=ranking,
            abstention_appropriate=not c.abstained,
            fidelity_score=1.0 if supported else 0.5,
            reasoning="Julgamento determinístico por presença de termos gold nas evidências.",
        )
    return verdicts


def main() -> int:
    parser = argparse.ArgumentParser(description="Cortex LLM Judge CLI")
    parser.add_argument("--export", action="store_true", help="Exportar lote para judge_inbox.json")
    parser.add_argument("--eval", action="store_true", help="Avaliar vereditos de judge_verdicts.json")
    parser.add_argument("--heuristic", action="store_true", help="Gerar vereditos heurísticos de fallback")
    parser.add_argument("--manifest", type=Path, default=Path("cortex/benchmarks/corpora/manifests/dogfooding_v1.json"))
    parser.add_argument("--inbox", type=Path, default=Path("artifacts/judge_inbox.json"))
    parser.add_argument("--verdicts", type=Path, default=Path("artifacts/judge_verdicts.json"))
    parser.add_argument("--report-out", type=Path, default=Path("artifacts/judge_report.json"))
    args = parser.parse_args()

    from cortex.benchmarks.adapters.cortex import CortexAdapter
    from cortex.benchmarks.schema import instance_from_dict

    manifest_data = json.loads(args.manifest.read_text(encoding="utf-8"))
    corpus_file = (args.manifest.parent / manifest_data["corpus"]).resolve()
    instances = [
        instance_from_dict(json.loads(line))
        for line in corpus_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    adapter = CortexAdapter()
    results = []
    for inst in instances:
        adapter.setup(inst)
        adapter.ingest(inst)
        results.append(adapter.query(inst))
        adapter.teardown()

    cases = build_judge_cases(instances, results)

    if args.export:
        out = export_judge_inbox(cases, args.inbox)
        print(f"Lote exportado para {out} ({len(cases)} casos)")
        return 0

    if args.heuristic:
        v_dict = generate_heuristic_verdicts(cases)
        args.verdicts.parent.mkdir(parents=True, exist_ok=True)
        payload = {"verdicts": [v.to_dict() for v in v_dict.values()]}
        args.verdicts.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Vereditos heurísticos gerados em {args.verdicts}")

    if args.eval or args.heuristic:
        verdicts = load_verdicts(args.verdicts)
        metrics = evaluate_judge_metrics(cases, verdicts)
        args.report_out.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(metrics, indent=2, ensure_ascii=False))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
