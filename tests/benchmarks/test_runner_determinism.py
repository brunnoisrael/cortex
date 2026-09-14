from pathlib import Path

from cortex.benchmarks.runner import run_benchmark


def test_runner_metrics_are_byte_deterministic(tmp_path):
    manifest = Path("cortex/benchmarks/corpora/manifests/mvp.json")
    first, second = tmp_path / "one", tmp_path / "two"
    run_benchmark(manifest, ["cortex", "bm25", "oracle"], first)
    run_benchmark(manifest, ["cortex", "bm25", "oracle"], second)
    assert (first / "metrics.jsonl").read_bytes() == (second / "metrics.jsonl").read_bytes()
    assert {p.name for p in first.iterdir()} == {"run_manifest.json", "metrics.jsonl", "summary.json", "errors.jsonl", "leakage.jsonl", "pareto.json", "report.md"}
