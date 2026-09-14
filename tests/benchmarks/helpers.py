from __future__ import annotations

from cortex.benchmarks.schema import BenchmarkInstance, sha256_prefixed


def make_case(case_id="case", *, task_type="exact_recall", abstain=False, invalid=None):
    history = [{"session_id": "s0", "timestamp": "2026-01-01T00:00:00Z", "events": [{"role": "user", "content": "PostgreSQL decision", "timestamp": "2026-01-01T00:01:00Z"}]}, {"session_id": "s1", "timestamp": "2026-01-02T00:00:00Z", "events": []}]
    gold = {"answer": "" if abstain else "PostgreSQL", "current_entities": [] if abstain else ["s0:0"], "invalid_entities": invalid or [], "gold_evidence": [] if abstain else ["s0:0"], "expected_abstention": abstain, "supersession_pairs": [["s0:0", "s1:0"]] if task_type == "cascade" else []}
    raw_history = history[:1]
    return BenchmarkInstance.model_validate({"schema": "cortex_memory_benchmark/v1", "id": case_id, "source": "internal", "source_revision": "test", "split": "regression", "domain": "software_project", "history": history, "cutoff": {"session_index": 1, "branch": "main"}, "query": {"text": "PostgreSQL"}, "task_type": task_type, "gold": gold, "constraints": {"max_context_tokens": 32, "allowed_future_data": False}, "checksums": {"history": sha256_prefixed(raw_history), "gold": sha256_prefixed(gold)}})
