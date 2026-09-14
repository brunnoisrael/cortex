"""Shared fixture builders for the benchmark suite.

Every helper builds a *valid* v1 instance, so a test that passes a malformed
case is making that choice explicitly instead of inheriting it.
"""

from __future__ import annotations

from typing import Any

from cortex.benchmarks.schema import BenchmarkInstance, instance_from_dict

ZEROS = "sha256:" + "0" * 64


def raw_case(case_id: str = "case", *, task_type: str = "exact_recall", abstain: bool = False,
             invalid: list[str] | None = None, history: list[dict[str, Any]] | None = None,
             query: str = "PostgreSQL", max_context_tokens: int = 32,
             **overrides: Any) -> dict[str, Any]:
    """A two-session case: one deciding session plus the cutoff boundary."""
    history = history or [
        {"session_id": "s0", "timestamp": "2026-01-01T00:00:00Z",
         "events": [{"role": "user", "content": "PostgreSQL decision", "timestamp": "2026-01-01T00:01:00Z"}]},
        {"session_id": "s1", "timestamp": "2026-01-02T00:00:00Z", "events": []},
    ]
    gold = {
        "answer": "" if abstain else "PostgreSQL",
        "current_entities": [] if abstain else ["s0:0"],
        "invalid_entities": invalid or [],
        "gold_evidence": [] if abstain else ["s0:0"],
        "expected_abstention": abstain,
        "supersession_pairs": [["s0:0", "s1:0"]] if task_type == "cascade" else [],
    }
    raw: dict[str, Any] = {
        "schema": "cortex_memory_benchmark/v1",
        "id": case_id,
        "source": "internal",
        "source_revision": "test",
        "split": "regression",
        "domain": "software_project",
        "history": history,
        "cutoff": {"session_index": len(history) - 1, "branch": "main"},
        "query": {"text": query},
        "task_type": task_type,
        "gold": gold,
        "constraints": {"max_context_tokens": max_context_tokens, "allowed_future_data": False},
        "checksums": {"history": ZEROS, "gold": ZEROS},
    }
    raw.update(overrides)
    return raw


def make_case(case_id: str = "case", **kwargs: Any) -> BenchmarkInstance:
    """A materialised instance: checksums are derived, never hand-written."""
    return instance_from_dict(raw_case(case_id, **kwargs), materialize=True)
