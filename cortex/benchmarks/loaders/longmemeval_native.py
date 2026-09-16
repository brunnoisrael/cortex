"""Normalize the raw LongMemEval *_cleaned.json* files (xiaowu0162/LongMemEval)
into the ``cortex_memory_benchmark/v1`` schema so the runner can evaluate
the Cortex retrieval pipeline on an independent, external benchmark.

Mapping decisions
-----------------
* ``question_type`` → ``task_type``

  LongMemEval (LME)           Cortex task_type
  ──────────────────────────  ─────────────────
  single-session-user         exact_recall
  single-session-assistant    exact_recall
  single-session-preference   exact_recall
  multi-session               aggregation
  temporal-reasoning          tracking
  knowledge-update            tracking

* Every LME session becomes one Cortex ``Session``; each turn becomes an
  ``Event``.  The ``question_date`` produces the synthetic cutoff session so
  the runner knows where the visible history ends.

* ``answer_session_ids`` are the gold-evidence identifiers.  Adapters retrieve
  ``session_id:event_index``; metrics project those IDs back to the session
  when ``metadata.evidence_grain`` is ``session``.  Turn-level gold is not
  available in the cleaned format — session grain is coarser but honest.

* ``gold.answer`` keeps the LME natural-language answer.  It is **not** copied
  into ``current_entities``: that field is an ID set compared against adapter
  ``selected`` IDs.  Putting the answer string there would zero every retrieval
  metric.

* The annotation_quality is ``exploratory`` because there is no kappa score.

* ``source_revision`` is the filename stem so manifests can pin a version.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from ..schema import (
    BenchmarkInstance,
    Checksums,
    Constraints,
    Cutoff,
    Event,
    Gold,
    Query,
    Session,
    sha256_prefixed,
)

# LME date format: "2023/05/20 (Sat) 02:21"
_LME_DATE_RE = re.compile(
    r"(?P<y>\d{4})/(?P<m>\d{2})/(?P<d>\d{2})\s+\([A-Za-z]+\)\s+(?P<H>\d{2}):(?P<M>\d{2})"
)

_QUESTION_TYPE_MAP = {
    "single-session-user": "exact_recall",
    "single-session-assistant": "exact_recall",
    "single-session-preference": "exact_recall",
    "multi-session": "aggregation",
    "temporal-reasoning": "tracking",
    "knowledge-update": "tracking",
}

MAX_CONTEXT_TOKENS = 4096


def _lme_date_to_iso(raw: str) -> str:
    m = _LME_DATE_RE.match(raw.strip())
    if not m:
        return "2023-01-01T00:00:00+00:00"
    return f"{m['y']}-{m['m']}-{m['d']}T{m['H']}:{m['M']}:00+00:00"


def _short_id(text: str, prefix: str) -> str:
    return prefix + "-" + hashlib.sha256(text.encode()).hexdigest()[:8]


def _turns_to_events(turns: list[dict[str, Any]], session_ts: str) -> list[Event]:
    events = []
    for turn in turns:
        role = turn.get("role", "user")
        if role not in {"user", "assistant", "system", "tool", "commit", "diff", "test"}:
            role = "user"
        events.append(Event(role=role, content=turn.get("content", ""), timestamp=session_ts))
    return events


def _build_checksums(history_until_cutoff: list[Session], gold: Gold) -> Checksums:
    return Checksums(
        history=sha256_prefixed(
            [s.model_dump(by_alias=True, mode="json") for s in history_until_cutoff]
        ),
        gold=sha256_prefixed(gold.model_dump(mode="json")),
    )


def normalize_longmemeval(
    path: Path,
    *,
    split: str = "dev",
    max_cases: int | None = None,
) -> list[BenchmarkInstance]:
    """Load *path* (raw LME _cleaned.json) and return normalised instances.

    Args:
        path: Path to the raw LME JSON file.
        split: The benchmark split label to assign to every case.
        max_cases: If set, only the first N cases are returned (useful for
            quick smoke-tests without loading 277 MB).
    """
    rows: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))
    source_revision = path.stem  # e.g. "longmemeval_s_cleaned"

    instances: list[BenchmarkInstance] = []
    for row in rows[:max_cases] if max_cases else rows:
        qid = row["question_id"]
        question_type = row.get("question_type", "single-session-user")
        task_type = _QUESTION_TYPE_MAP.get(question_type, "exact_recall")
        question_date_raw = row.get("question_date", "")
        question_ts = _lme_date_to_iso(question_date_raw)

        haystack_session_ids: list[str] = row["haystack_session_ids"]
        haystack_dates: list[str] = row.get("haystack_dates", [])
        haystack_sessions_raw: list[list[dict]] = row["haystack_sessions"]
        answer_session_ids: set[str] = set(row.get("answer_session_ids", []))

        # Build Cortex sessions from the haystack, in order.
        history: list[Session] = []
        gold_evidence_ids: list[str] = []

        for i, (sid, date_raw, turns) in enumerate(
            zip(haystack_session_ids, haystack_dates, haystack_sessions_raw)
        ):
            ts = _lme_date_to_iso(date_raw)
            events = _turns_to_events(turns, ts)
            history.append(Session(session_id=sid, timestamp=ts, events=events))
            if sid in answer_session_ids:
                gold_evidence_ids.append(sid)

        # Append a synthetic cutoff session so the runner knows where to cut.
        cutoff_sid = f"lme_cutoff_{qid}"
        cutoff_session = Session(
            session_id=cutoff_sid,
            timestamp=question_ts,
            events=[Event(role="system", content="[query boundary]", timestamp=question_ts)],
        )
        history.append(cutoff_session)
        cutoff_index = len(history) - 1  # the cutoff session is the LAST one

        answer_text = str(row.get("answer", "") or "")
        gold = Gold(
            answer=answer_text,
            accepted_answers=[answer_text] if answer_text else [],
            # Session IDs, not the NL answer: retrieval metrics compare ID sets.
            current_entities=list(gold_evidence_ids),
            invalid_entities=[],
            expected_abstention=False,
            gold_evidence=gold_evidence_ids,
            annotation_quality="exploratory",
            annotation_agreement={"kappa": 0.0},
        )

        visible = history[:cutoff_index]
        checksums = _build_checksums(visible, gold)

        instance = BenchmarkInstance(
            **{
                "schema": "cortex_memory_benchmark/v1",
                "id": f"lme-{qid}",
                "source": "longmemeval",
                "source_revision": source_revision,
                "split": split,
                "domain": "general_chat",
                "history": history,
                "cutoff": Cutoff(session_index=cutoff_index),
                "query": Query(text=row["question"]),
                "task_type": task_type,
                "gold": gold,
                "constraints": Constraints(max_context_tokens=MAX_CONTEXT_TOKENS),
                "checksums": checksums,
                "metadata": {
                    "lme_question_type": question_type,
                    "lme_question_date": question_date_raw,
                    "lme_answer_session_ids": list(answer_session_ids),
                    "evidence_grain": "session",
                    "external_control": True,
                    "transform": "longmemeval_native/v1",
                },
            }
        )
        instances.append(instance)

    return instances


def export_jsonl(instances: list[BenchmarkInstance], out: Path) -> None:
    """Persist normalised instances as a JSONL corpus file."""
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(inst.model_dump(by_alias=True, mode="json"), ensure_ascii=False, separators=(",", ":"))
        for inst in instances
    ]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Normalize a raw LME _cleaned.json into JSONL.")
    parser.add_argument("input", type=Path, help="Path to *_cleaned.json")
    parser.add_argument("output", type=Path, help="Destination .jsonl path")
    parser.add_argument("--split", default="dev", choices=["dev", "eval", "regression"])
    parser.add_argument("--max-cases", type=int, default=None, help="Limit number of cases")
    args = parser.parse_args()

    print(f"Loading {args.input} ...", file=sys.stderr)
    insts = normalize_longmemeval(args.input, split=args.split, max_cases=args.max_cases)
    print(f"Normalised {len(insts)} instances → {args.output}", file=sys.stderr)
    export_jsonl(insts, args.output)
    print("Done.", file=sys.stderr)
