import json

from cortex.benchmarks.loaders.swebench import load_swebench


def test_swebench_rejects_invalid_normalized_cutoff(tmp_path):
    row = {"instance_id": "x", "patch": "SECRET_PATCH", "test_patch": "SECRET_TEST", "normalized": {
        "schema": "cortex_memory_benchmark/v1", "id": "x", "source": "swebench", "source_revision": "base", "split": "dev", "domain": "software_project",
        "history": [{"session_id": "s0", "timestamp": "2026-01-01T00:00:00Z", "events": []}], "cutoff": {"session_index": 0, "branch": "main"},
        "query": {"text": "fix"}, "task_type": "exact_recall", "gold": {"expected_abstention": False, "gold_evidence": []},
        "constraints": {"max_context_tokens": 10, "allowed_future_data": False}, "checksums": {"history": "sha256:" + "0" * 64, "gold": "sha256:" + "0" * 64}}}
    path = tmp_path / "swe.json"
    path.write_text(json.dumps([row]), encoding="utf-8")
    try:
        load_swebench(path)
    except Exception as exc:
        assert "cutoff" in str(exc).lower() or "checksum" in str(exc).lower()
