import json
from pathlib import Path

import pytest

from cortex.benchmarks.corpora.build_internal import REVISION
from cortex.benchmarks.manifest import load_manifest
from cortex.benchmarks.runner import run_benchmark

ARTIFACTS = {"run_manifest.json", "metrics.jsonl", "summary.json", "errors.jsonl",
             "leakage.jsonl", "pareto.json", "report.md", "latency.jsonl"}


def test_runner_metrics_are_byte_deterministic(tmp_path):
    """Gate G0: two clean runs of the same manifest agree byte for byte.

    ``latency.jsonl`` is the only file allowed to differ, because plan §7
    explicitly keeps latency and log timestamps out of the deterministic
    payload.
    """
    manifest = Path("cortex/benchmarks/corpora/manifests/memory_v1.json")
    first, second = tmp_path / "one", tmp_path / "two"
    run_benchmark(manifest, ["cortex", "bm25", "oracle"], first)
    run_benchmark(manifest, ["cortex", "bm25", "oracle"], second)
    assert (first / "metrics.jsonl").read_bytes() == (second / "metrics.jsonl").read_bytes()
    assert (first / "summary.json").read_bytes() == (second / "summary.json").read_bytes()
    assert (first / "run_manifest.json").read_bytes() == (second / "run_manifest.json").read_bytes()
    assert {p.name for p in first.iterdir()} == ARTIFACTS


def test_latency_is_reported_separately_and_never_in_metrics(tmp_path):
    manifest = Path("cortex/benchmarks/corpora/manifests/memory_v1.json")
    out = tmp_path / "run"
    run_benchmark(manifest, ["cortex"], out)
    metrics = (out / "metrics.jsonl").read_text(encoding="utf-8")
    assert "latency" not in metrics and "elapsed" not in metrics
    latency = [line for line in (out / "latency.jsonl").read_text(encoding="utf-8").splitlines() if line]
    assert latency, "efficiency data must be reported, not dropped"
    assert '"case_id"' in latency[0] and '"phase_ms"' in latency[0]


def test_run_manifest_records_the_freeze(tmp_path):
    import json

    manifest = Path("cortex/benchmarks/corpora/manifests/memory_v1.json")
    out = tmp_path / "run"
    run_benchmark(manifest, ["bm25"], out)
    document = json.loads((out / "run_manifest.json").read_text(encoding="utf-8"))
    frozen = document["frozen"]
    assert frozen["splits"]["dev"] and frozen["revisions"] == {"internal": REVISION}
    assert document["network_enabled"] is False


def test_adversarial_corpus_runs_without_silent_failures(tmp_path):
    """The adversarial corpus is a diagnostic: it runs clean, but its failures
    must be visible in the metrics instead of averaged away."""
    manifest = Path("cortex/benchmarks/corpora/manifests/memory_v1_adversarial.json")
    out = tmp_path / "adversarial"
    summary = run_benchmark(manifest, ["cortex", "bm25", "raw_context", "no_memory", "oracle"], out)
    assert summary["errors"] == 0 and summary["leakage"] == 0
    assert "adv-dedup-absorbs-update" in (out / "metrics.jsonl").read_text(encoding="utf-8")


def test_opt_in_registry_records_complete_execution_provenance(tmp_path):
    """Operational metadata is append-only and separate from G0 artifacts."""
    manifest = Path("cortex/benchmarks/corpora/manifests/mvp.json")
    registry = tmp_path / "published" / "experiments.jsonl"
    result = run_benchmark(manifest, ["bm25"], tmp_path / "run", experiment_registry=registry)

    assert result["experiment_registry"] == str(registry)
    records = [json.loads(line) for line in registry.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 1
    record = records[0]
    assert record["schema"] == "cortex_benchmark_experiment/v1"
    assert record["classification"] == "exploratory"
    assert record["adapters"] == ["bm25"]
    assert record["corpus"]["frozen_hash"]
    assert record["context_budget"]["minimum"] > 0
    assert record["models"]["reader"] == "none (retrieval-only benchmark)"
    assert set(record["artifacts"]) == {
        "run_manifest.json", "metrics.jsonl", "summary.json", "errors.jsonl",
        "leakage.jsonl", "pareto.json", "report.md",
    }


def test_manifest_requires_evidence_classification(tmp_path):
    source = Path("cortex/benchmarks/corpora/manifests/mvp.json")
    raw = json.loads(source.read_text(encoding="utf-8"))
    raw.pop("evidence_classification")
    manifest = tmp_path / "missing-classification.json"
    manifest.write_text(json.dumps(raw), encoding="utf-8")

    with pytest.raises(Exception, match="evidence_classification"):
        load_manifest(manifest)
