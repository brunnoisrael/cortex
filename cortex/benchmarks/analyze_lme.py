"""Post-run gap analysis for LongMemEval (diagnostic, not confirmatory).

Reads ``metrics.jsonl`` from a runner output directory and groups retrieval
and extraction scores by LME ``question_type``.  That split is the useful
readout: heuristic extractors were written for engineering ADRs/fixes, not
personal chat facts.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


PRIMARY = ("recall_at_k", "extraction_recall", "precision_at_k", "mrr", "set_f1",
           "current_state_accuracy", "abstention_recall")


def load_rows(metrics_path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in metrics_path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def analyze(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_adapter: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    by_qtype: dict[str, dict[str, dict[str, list[float]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    by_task: dict[str, dict[str, dict[str, list[float]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    cases: dict[str, int] = defaultdict(int)
    seen_case: set[tuple[str, str]] = set()
    for row in rows:
        adapter, metric, value = row["adapter"], row["metric"], float(row["value"])
        qtype = str(row.get("question_type") or row.get("task_type") or "unknown")
        task = str(row.get("task_type") or "unknown")
        by_adapter[adapter][metric].append(value)
        by_qtype[qtype][adapter][metric].append(value)
        by_task[task][adapter][metric].append(value)
        key = (adapter, row["case_id"])
        if key not in seen_case:
            seen_case.add(key)
            cases[adapter] += 1

    def flatten(grouped: dict) -> dict:
        out: dict[str, Any] = {}
        for outer, adapters in sorted(grouped.items()):
            out[outer] = {
                adapter: {metric: round(_mean(vals), 4) for metric, vals in sorted(metrics.items())
                          if metric in PRIMARY}
                for adapter, metrics in sorted(adapters.items())
            }
        return out

    overview = {
        adapter: {metric: round(_mean(vals), 4) for metric, vals in sorted(metrics.items()) if metric in PRIMARY}
        for adapter, metrics in sorted(by_adapter.items())
    }
    return {
        "schema": "cortex_lme_gap_analysis/v1",
        "n_cases": dict(cases),
        "overall": overview,
        "by_question_type": flatten(by_qtype),
        "by_task_type": flatten(by_task),
    }


def render_markdown(analysis: dict[str, Any]) -> str:
    lines = [
        "# LongMemEval-S — gap analysis (diagnostic)",
        "",
        "Classe de claim: **exploratory**.  Estes números não promovem o produto;",
        "eles mostram onde a extração heurística (ADRs, fixes, intenções) não cobre",
        "o domínio de chat pessoal do LongMemEval.",
        "",
        f"- Casos por adapter: `{json.dumps(analysis['n_cases'], sort_keys=True)}`",
        "",
        "## Overall (média)",
        "",
        "| Adapter | recall@k | extraction_recall | precision@k | MRR | set_f1 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for adapter, metrics in analysis["overall"].items():
        lines.append(
            f"| {adapter} | {metrics.get('recall_at_k', 0):.4f} | "
            f"{metrics.get('extraction_recall', float('nan'))} | "
            f"{metrics.get('precision_at_k', 0):.4f} | {metrics.get('mrr', 0):.4f} | "
            f"{metrics.get('set_f1', 0):.4f} |"
        )
    lines += ["", "## Por question_type do LME", "",
              "| question_type | Adapter | recall@k | extraction_recall | set_f1 |",
              "|---|---|---:|---:|---:|"]
    for qtype, adapters in analysis["by_question_type"].items():
        for adapter, metrics in adapters.items():
            ext = metrics.get("extraction_recall")
            ext_s = f"{ext:.4f}" if isinstance(ext, float) else "n/a"
            lines.append(
                f"| {qtype} | {adapter} | {metrics.get('recall_at_k', 0):.4f} | "
                f"{ext_s} | {metrics.get('set_f1', 0):.4f} |"
            )
    lines += [
        "",
        "## Como ler",
        "",
        "- `extraction_recall` baixo no Cortex: os extratores não materializaram",
        "  conhecimento nas sessões ouro (o elo fraco esperado).",
        "- `recall@k` do BM25 alto e do Cortex baixo: o ranking lexical acha a",
        "  sessão, a destilação heurística não.",
        "- `recall@k` baixo em todos: a query LME não overlap lexicalmente com o",
        "  turno ouro (paráfrase / temporal / preferência).",
        "",
    ]
    return "\n".join(lines)


def write_analysis(report_out: Path) -> dict[str, Any]:
    analysis = analyze(load_rows(report_out / "metrics.jsonl"))
    (report_out / "gap_analysis.json").write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (report_out / "gap_analysis.md").write_text(render_markdown(analysis), encoding="utf-8")
    return analysis


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-out", type=Path, required=True)
    args = parser.parse_args(argv)
    analysis = write_analysis(args.report_out)
    print(json.dumps({"n_cases": analysis["n_cases"], "overall": analysis["overall"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
