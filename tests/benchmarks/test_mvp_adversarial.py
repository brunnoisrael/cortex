from pathlib import Path

from cortex.benchmarks.runner import run_benchmark


def test_mvp_has_no_silent_failures(tmp_path):
    result = run_benchmark(Path("cortex/benchmarks/corpora/manifests/mvp.json"), ["cortex", "bm25", "raw_context", "no_memory", "oracle"], tmp_path)
    assert result["cases"] == 10
    assert result["errors"] == 0
    assert result["leakage"] == 0
