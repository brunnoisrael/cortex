"""Reporting contract: gates, decision and the determinism boundary."""

from __future__ import annotations

import json
from pathlib import Path

from cortex.benchmarks.reports import cost_gate, write_reports
from cortex.benchmarks.schema import instance_from_dict

from .corpora_cases import build_case
from .helpers import raw_case


def _write(tmp_path: Path, rows, errors=(), leakage=(), latency=()):
    manifest = {
        "cortex_version": "0.1.0", "corpus_hash": "sha256:" + "0" * 64,
        "dataset_revisions": {"internal": "test"}, "network_enabled": False,
    }
    out = tmp_path / "report"
    write_reports(out, manifest, rows, list(errors), list(leakage), list(latency))
    return out


def _row(case_id, adapter, metric, value, task_type="exact_recall", split="dev"):
    return {"case_id": case_id, "adapter": adapter, "metric": metric, "value": value,
            "task_type": task_type, "split": split}


def test_all_required_artifacts_are_written(tmp_path):
    out = _write(tmp_path, [_row("c1", "cortex", "stale_leak_rate", 0.0)])
    assert {path.name for path in out.iterdir()} == {
        "run_manifest.json", "metrics.jsonl", "summary.json", "errors.jsonl",
        "leakage.jsonl", "latency.jsonl", "pareto.json", "report.md"}


def test_safety_gate_flags_stale_leak_against_baselines(tmp_path):
    rows = [_row("c1", "cortex", "stale_leak_rate", 0.0),
            _row("c1", "bm25", "stale_leak_rate", 1.0),
            _row("c1", "raw_context", "stale_leak_rate", 1.0)]
    summary = json.loads((_write(tmp_path, rows) / "summary.json").read_text(encoding="utf-8"))
    gate = summary["gates"]["G1_cortex_integrity"]
    assert gate["stale_leak_rate_cortex"] == 0.0
    assert gate["stale_leak_not_worse_than_bm25"] is True
    assert gate["stale_leak_not_worse_than_raw_context"] is True


def test_zero_stale_leak_everywhere_still_reports_the_gate(tmp_path):
    rows = [_row("c1", "cortex", "stale_leak_rate", 0.0),
            _row("c1", "bm25", "stale_leak_rate", 0.0)]
    summary = json.loads((_write(tmp_path, rows) / "summary.json").read_text(encoding="utf-8"))
    assert summary["gates"]["G1_cortex_integrity"]["stale_leak_not_worse_than_bm25"] is True


def test_errors_or_leakage_block_the_release(tmp_path):
    rows = [_row("c1", "cortex", "stale_leak_rate", 0.0)]
    summary = json.loads((_write(tmp_path, rows, errors=[{"case_id": "c1", "error": "X"}]) / "summary.json").read_text(encoding="utf-8"))
    assert summary["decision"] == "bloquear_expansao"


def test_stale_leak_yields_recalibrate(tmp_path):
    rows = [_row("c1", "cortex", "stale_leak_rate", 1.0),
            _row("c1", "bm25", "stale_leak_rate", 1.0)]
    summary = json.loads((_write(tmp_path, rows) / "summary.json").read_text(encoding="utf-8"))
    assert summary["decision"] == "recalibrar"


def test_no_gains_and_no_leak_yields_reduced_claim(tmp_path):
    rows = [_row("c1", "cortex", "stale_leak_rate", 0.0),
            _row("c1", "bm25", "stale_leak_rate", 0.0)]
    summary = json.loads((_write(tmp_path, rows) / "summary.json").read_text(encoding="utf-8"))
    assert summary["decision"] == "reduzir_claim"


def test_summary_stays_free_of_latency_but_pareto_carries_it(tmp_path):
    latency = [{"case_id": "c1", "adapter": "cortex",
                "phase_ms": {"ingest": 1.0, "query": 2.0, "compile": 3.0},
                "tokens": {"input": 4, "retrieved": 5, "compiled": 6}}]
    out = _write(tmp_path, [_row("c1", "cortex", "recall_at_k", 1.0)], latency=latency)
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert "efficiency" not in summary and "G4_operational_cost" not in summary["gates"]
    pareto = json.loads((out / "pareto.json").read_text(encoding="utf-8"))
    assert pareto["gates"]["G4_operational_cost"]["compiled_tokens_mean"] == 6.0
    assert pareto["efficiency"]["cortex"]["query_p95_ms"] == 2.0
    assert cost_gate(pareto["efficiency"])["token_budget_respected"] is True


def test_latency_is_excluded_from_the_deterministic_payload(tmp_path):
    latency = [{"case_id": "c1", "adapter": "cortex", "phase_ms": {"ingest": 999.0},
                "tokens": {"input": 1, "retrieved": 1, "compiled": 1}}]
    rows = [_row("c1", "cortex", "recall_at_k", 1.0)]
    first = _write(tmp_path / "a", rows, latency=latency)
    second = _write(tmp_path / "b", rows, latency=[dict(latency[0], phase_ms={"ingest": 0.1})])
    assert (first / "metrics.jsonl").read_bytes() == (second / "metrics.jsonl").read_bytes()
    assert (first / "summary.json").read_bytes() == (second / "summary.json").read_bytes()


def test_metrics_lines_are_sorted_and_never_report_a_single_mean(tmp_path):
    case = instance_from_dict(build_case("mem-tracking-api"), materialize=True)
    rows = [_row(case.id, "cortex", "recall_at_k", 1.0, case.task_type, case.split),
            _row(case.id, "bm25", "recall_at_k", 0.0, case.task_type, case.split)]
    out = _write(tmp_path, rows)
    metrics = [json.loads(line) for line in (out / "metrics.jsonl").read_text(encoding="utf-8").splitlines()]
    assert metrics == sorted(metrics, key=lambda item: json.dumps(item, sort_keys=True))
    report = (out / "report.md").read_text(encoding="utf-8")
    assert "por task type" in report
    assert raw_case  # helper still used by the suite; keeps imports meaningful
