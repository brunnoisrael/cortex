"""Stable JSONL and Markdown reporting for a benchmark run."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .stats import paired_bootstrap_ci


def _dump(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def write_reports(out: Path, manifest: dict[str, Any], rows: list[dict[str, Any]], errors: list[dict[str, Any]], leakage: list[dict[str, Any]]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    _dump(out / "run_manifest.json", manifest)
    with (out / "metrics.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for row in sorted(rows, key=lambda item: (item["case_id"], item["adapter"], item["metric"])):
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    with (out / "errors.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for row in errors:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    with (out / "leakage.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for row in leakage:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")

    grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in rows:
        grouped[(row["adapter"], row["metric"])].append(row["value"])
    summary: dict[str, Any] = {"schema": "cortex_benchmark_summary/v1", "endpoints": {}, "by_task_type": {},
                               "paired_comparisons": {}, "gates": {}, "coverage": {}, "decision": "diagnostic_only"}
    for (adapter, metric), values in sorted(grouped.items()):
        summary["endpoints"].setdefault(adapter, {})[metric] = {"mean": sum(values) / len(values), "n": len(values), "confirmatory": len(values) >= 5}
        for row in (item for item in rows if item["adapter"] == adapter and item["metric"] == metric):
            summary["by_task_type"].setdefault(row["task_type"], {}).setdefault(adapter, {}).setdefault(metric, []).append(row["value"])
    for task, adapters in summary["by_task_type"].items():
        for adapter, metrics in adapters.items():
            for metric, values in metrics.items():
                metrics[metric] = {"mean": sum(values) / len(values), "n": len(values), "confirmatory": len(values) >= 5}
    for metric in sorted({row["metric"] for row in rows}):
        cortex = {row["case_id"]: row["value"] for row in rows if row["adapter"] == "cortex" and row["metric"] == metric}
        for baseline in ("bm25", "raw_context"):
            other = {row["case_id"]: row["value"] for row in rows if row["adapter"] == baseline and row["metric"] == metric}
            common = sorted(set(cortex) & set(other))
            if len(common) >= 2:
                diff, low, high = paired_bootstrap_ci([cortex[key] for key in common], [other[key] for key in common], n_resamples=1000)
                summary["paired_comparisons"][f"cortex_vs_{baseline}:{metric}"] = {"n": len(common), "diff": diff, "ci_low": low, "ci_high": high, "confirmatory": len(common) >= 5}
    summary["gates"] = {"stale_leak_rate": {adapter: summary["endpoints"].get(adapter, {}).get("stale_leak_rate", {}).get("mean") for adapter in ("cortex", "bm25", "raw_context")},
                         "false_certainty_reported_per_case": any(row["metric"] == "false_certainty_rate" for row in rows)}
    _dump(out / "summary.json", summary)
    _dump(out / "pareto.json", _pareto(rows))
    (out / "report.md").write_text(_markdown(summary, errors, leakage), encoding="utf-8")


def _pareto(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_adapter: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        by_adapter[row["adapter"]][row["metric"]].append(row["value"])
    return {adapter: {metric: sum(values) / len(values) for metric, values in sorted(metrics.items())}
            for adapter, metrics in sorted(by_adapter.items())}


def _markdown(summary: dict[str, Any], errors: list[dict[str, Any]], leakage: list[dict[str, Any]]) -> str:
    lines = ["# Cortex memory benchmark v1", "", "## Endpoints", "", "| Adapter | Endpoint | Mean | n | Confirmatory |", "|---|---|---:|---:|---|"]
    for adapter, metrics in summary["endpoints"].items():
        for metric, value in metrics.items():
            lines.append(f"| {adapter} | {metric} | {value['mean']:.4f} | {value['n']} | {value['confirmatory']} |")
    lines += ["", "## Safety", "", f"- Explicit errors: {len(errors)}", f"- Leakage events: {len(leakage)}",
              "- Product decision: diagnostic only until external datasets and confirmatory power are frozen.",
              "- Stale-leak gate and paired intervals are reported in `summary.json`; this MVP does not make a product claim.", ""]
    return "\n".join(lines)
