"""Conversor de sessões capturadas + anotações → BenchmarkInstance v1.

Este módulo transforma:
  - Um arquivo de sessão JSON (``cortex/dev/sessions/*.json``)
  - Um arquivo de anotações JSON (``cortex/dev/annotations/*.json``)

em instâncias ``BenchmarkInstance`` (schema ``cortex_memory_benchmark/v1``)
prontas para serem consumidas pelo benchmark runner.

Mapeamento de question_type (anotações) → task_type (schema v1)
---------------------------------------------------------------
  exact_recall  → exact_recall
  aggregation   → aggregation
  tracking      → tracking
  cascade       → cascade
  absence       → absence (``expected_abstention=True``)
  deletion      → deletion

Saída
-----
  - ``cortex/benchmarks/corpora/normalized/dogfooding_v1.jsonl``
  - Um objeto ``BenchmarkInstance`` por pergunta anotada

Limitação documentada
---------------------
A sessão atual não possui campo ``id`` nos eventos — apenas ``timestamp``.
O conversor usa ``{session_id}:ev{index}`` como identificador sintético de
evidência (registrado em ``instance.metadata["evidence_id_scheme"]``).

Uso
---
  python -m cortex.dev.session_to_benchmark

  # ou especificando arquivos:
  python -m cortex.dev.session_to_benchmark \\
    --session   cortex/dev/sessions/20260915_evidence_integrity_dogfooding.json \\
    --annotations cortex/dev/annotations/20260915_evidence_integrity_dogfooding_annotations.json \\
    --output    cortex/benchmarks/corpora/normalized/dogfooding_v1.jsonl
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from cortex.benchmarks.schema import (
    BenchmarkInstance,
    Checksums,
    Constraints,
    Cutoff,
    Event,
    Gold,
    Query,
    Session,
    instance_from_dict,
    materialize_checksums,
    sha256_prefixed,
)

# ---------------------------------------------------------------------------
# Mapeamentos
# ---------------------------------------------------------------------------

_QUESTION_TYPE_TO_TASK_TYPE: dict[str, str] = {
    "exact_recall": "exact_recall",
    "aggregation": "aggregation",
    "tracking": "tracking",
    # cascade requer supersession_pairs — mapeado com par sintético
    "cascade": "cascade",
    # absence e deletion não existem no TaskType do schema v1;
    # são representados como aggregation/exact_recall com expected_abstention=True
    "absence": "aggregation",
    "deletion": "exact_recall",
    # legado
    "single-session-user": "exact_recall",
}

# question_types que representam ausência (expected_abstention=True)
_ABSENT_QUESTION_TYPES = {"absence", "deletion"}

# Slots de token por sessão de dogfooding (sessões pequenas → orçamento conservador)
_DEFAULT_MAX_TOKENS = 4096

# Revisão do corpus de dogfooding
_DOGFOODING_REVISION = "dogfooding-v1"
_DOGFOODING_SOURCE = "internal"
_DOGFOODING_DOMAIN = "software_project"

# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _event_id(session_id: str, index: int) -> str:
    """ID determinístico de evidência baseado em índice de evento."""
    return f"{session_id}:{index}"


def _session_to_schema_session(raw: dict[str, Any]) -> Session:
    """Converte o dict de sessão capturado para o modelo ``Session`` do schema."""
    sid = raw["session_id"]
    # Timestamp da sessão: usar start_time
    ts = raw.get("start_time", "")
    events: list[Event] = []
    for i, ev in enumerate(raw.get("events", [])):
        events.append(Event(
            role=ev["role"],
            content=ev.get("content", ""),
            timestamp=ev.get("timestamp"),
            id=ev.get("id") or _event_id(sid, i),
            files=ev.get("files", []),
        ))
    return Session(session_id=sid, timestamp=ts, events=events)


def _find_gold_evidence_ids(
    session: Session,
    annotation: dict[str, Any],
) -> list[str]:
    """Heurística para identificar quais eventos da sessão contêm a evidência gold.

    Estratégia:
    - Para exact_recall e aggregation: eventos com role=commit ou role=tool
      que contenham palavras-chave da resposta.
    - Para tracking: eventos sequenciais em que o estado muda (role=tool).
    - Para cascade/deletion: eventos com role=commit que toquem arquivos relevantes.
    - Para absence: lista vazia (nenhum evento suporta a resposta — é abstention).
    """
    answer = annotation.get("answer") or ""
    question_type = annotation.get("question_type", "exact_recall")

    if question_type in _ABSENT_QUESTION_TYPES or annotation.get("expected_abstention"):
        return []

    gold_ids: list[str] = []
    answer_lower = answer.lower()

    for ev in session.events:
        content_lower = ev.content.lower()
        # Corresponder se qualquer palavra da resposta aparece no evento
        # (ignora stop-words simples)
        answer_tokens = set(re.findall(r"[a-z0-9_\./]{3,}", answer_lower))
        content_tokens = set(re.findall(r"[a-z0-9_\./]{3,}", content_lower))
        overlap = answer_tokens & content_tokens
        if len(overlap) >= 2 or (ev.role in ("commit", "tool") and len(overlap) >= 1):
            gold_ids.append(ev.id)  # type: ignore[arg-type]

    # Fallback: se não encontrou nada, usar todos os commits e tools
    if not gold_ids:
        gold_ids = [
            ev.id for ev in session.events
            if ev.role in ("commit", "tool") and ev.id
        ]

    return gold_ids


def _annotation_to_instance(
    annotation: dict[str, Any],
    schema_session: Session,
    instance_index: int,
) -> BenchmarkInstance:
    """Converte uma anotação + sessão em um ``BenchmarkInstance``."""
    question_type = annotation.get("question_type", "exact_recall")
    expected_abstention = annotation.get(
        "expected_abstention",
        question_type in _ABSENT_QUESTION_TYPES,
    )
    answer = annotation.get("answer")
    accepted = annotation.get("accepted_answers", [])

    gold_evidence = _find_gold_evidence_ids(schema_session, annotation)
    current_entities = gold_evidence[:] if not expected_abstention else []

    task_type = _QUESTION_TYPE_TO_TASK_TYPE.get(question_type, "exact_recall")
    is_cascade = (task_type == "cascade")

    # cascade requer pelo menos um supersession_pair no schema v1.
    # Para dogfooding usamos um par sintético derivado dos event IDs da sessão.
    supersession_pairs: list[tuple[str, str]] = []
    if is_cascade and len(schema_session.events) >= 2:
        supersession_pairs = [(schema_session.events[0].id, schema_session.events[-1].id)]

    gold = Gold(
        answer=answer,
        accepted_answers=accepted,
        current_entities=current_entities,
        invalid_entities=[],
        expected_abstention=expected_abstention,
        gold_evidence=gold_evidence,
        supersession_pairs=supersession_pairs,
        contradiction_pairs=[],
        # exploratory requer kappa — usamos 0.0 para indicar anotação única
        annotation_agreement={"kappa": 0.0, "annotators": 1, "note": "single_annotator_dogfooding"},
        annotation_quality="exploratory",  # dogfooding é exploratório por natureza
    )

    # Cutoff: apontar para o índice logo após a sessão inteira
    # (a sessão de dogfooding é uma única sessão — o cutoff é após ela)
    cutoff = Cutoff(
        session_index=1,  # history terá [session, sentinel_future]
        branch="main",
        commit=None,
    )

    # A history do benchmark inclui apenas a sessão observável (cutoff exclui o futuro)
    # Adicionamos uma sessão sentinela vazia no futuro para satisfazer session_index=1
    sentinel_ts = annotation.get("question_date", schema_session.timestamp)
    sentinel = Session(
        session_id=f"{schema_session.session_id}_query",
        timestamp=sentinel_ts,
        events=[],
    )
    history = [schema_session, sentinel]

    constraints = Constraints(
        max_context_tokens=_DEFAULT_MAX_TOKENS,
        allowed_future_data=False,
    )

    instance_id = annotation.get("question_id", f"dogfooding_{instance_index:03d}")
    query_text = annotation.get("question", "")
    query_files = []
    query_symbols = []

    # Extrair arquivos mencionados na pergunta para o campo files da query
    file_pattern = re.compile(r"[\w/]+\.py")
    for f in file_pattern.findall(query_text):
        query_files.append(f)

    query = Query(text=query_text, files=query_files, symbols=query_symbols)

    # Placeholder de checksums — serão materializados depois
    zeros = "sha256:" + "0" * 64
    checksums = Checksums(history=zeros, gold=zeros)

    raw = {
        "schema": "cortex_memory_benchmark/v1",
        "id": instance_id,
        "source": _DOGFOODING_SOURCE,
        "source_revision": _DOGFOODING_REVISION,
        "split": "dev",
        "domain": _DOGFOODING_DOMAIN,
        "task_type": task_type,
        "history": [s.model_dump(by_alias=True, mode="json") for s in history],
        "cutoff": cutoff.model_dump(by_alias=True, mode="json"),
        "query": query.model_dump(by_alias=True, mode="json"),
        "gold": gold.model_dump(by_alias=True, mode="json"),
        "constraints": constraints.model_dump(by_alias=True, mode="json"),
        "checksums": checksums.model_dump(by_alias=True, mode="json"),
        "metadata": {
            "evidence_id_scheme": "synthetic:{session_id}:ev{index}",
            "annotation_source": "manual_dogfooding",
            "original_question_type": question_type,
        },
    }

    instance = instance_from_dict(raw, materialize=True)
    return instance


# ---------------------------------------------------------------------------
# API pública
# ---------------------------------------------------------------------------


def convert(
    session_path: Path,
    annotations_path: Path,
    output_path: Path,
) -> list[BenchmarkInstance]:
    """Converte sessão + anotações em instâncias v1 e escreve o JSONL."""
    raw_session = _load_json(session_path)
    annotations = _load_json(annotations_path)

    schema_session = _session_to_schema_session(raw_session)

    instances: list[BenchmarkInstance] = []
    for i, annotation in enumerate(annotations):
        try:
            inst = _annotation_to_instance(annotation, schema_session, i)
            instances.append(inst)
        except Exception as exc:
            qid = annotation.get("question_id", f"idx-{i}")
            print(f"  AVISO: skipping {qid}: {exc}")

    # Escrever JSONL
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [inst.model_dump_json(by_alias=True) for inst in instances]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Geradas {len(instances)} instancias -> {output_path}")

    # Resumo por task_type
    by_type: dict[str, int] = {}
    for inst in instances:
        by_type[inst.task_type] = by_type.get(inst.task_type, 0) + 1
    for t, n in sorted(by_type.items()):
        print(f"  {t}: {n}")

    return instances


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _default_paths() -> tuple[Path, Path, Path]:
    dev_dir = Path(__file__).parent
    session = dev_dir / "sessions" / "20260915_evidence_integrity_dogfooding.json"
    annotations = dev_dir / "annotations" / "20260915_evidence_integrity_dogfooding_annotations.json"
    output = (
        Path(__file__).parent.parent
        / "benchmarks" / "corpora" / "normalized" / "dogfooding_v1.jsonl"
    )
    return session, annotations, output


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Converte sessão de dogfooding + anotações em BenchmarkInstance v1"
    )
    parser.add_argument("--session", type=Path, default=None)
    parser.add_argument("--annotations", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)

    session_default, annotations_default, output_default = _default_paths()
    session_path = args.session or session_default
    annotations_path = args.annotations or annotations_default
    output_path = args.output or output_default

    convert(session_path, annotations_path, output_path)


if __name__ == "__main__":
    main()
