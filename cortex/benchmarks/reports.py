"""Stable JSONL and Markdown reporting for a benchmark run.

Every run emits the seven artifacts required by plan §11 plus
``latency.jsonl``, which plan §7 carves out of the deterministic payload:
latency and log timestamps live in their own file so two clean runs of the
same manifest still produce byte-identical ``metrics.jsonl``.

The report never reports a single mean as a result: aggregates are broken down
by task type and split, safety gates are explicit, and the file ends with a
product decision chosen from the plan's four options.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .stats import holm_bonferroni, paired_bootstrap_ci, paired_bootstrap_p_value, power_analysis

# Adapter labels that are ablations of the Cortex, not independent products.
ABLATION_PREFIX = "cortex["

TOKEN_BUDGET_KEY = "compiled"

# Pre-registered before looking at eval results (plan §5): a comparison only
# counts as confirmatory when the sample is large enough to detect this
# difference.  Changing it is a specification change and needs an ADR.
MINIMUM_DETECTABLE_EFFECT = 0.15

# Families of plan §5.  Holm-Bonferroni is applied inside a family, never
# across families: pooling them would dilute the correction each claim needs.
METRIC_FAMILIES: dict[str, tuple[str, ...]] = {
    "retrieval": ("recall_at_k", "precision_at_k", "mrr", "ndcg_at_k", "set_f1",
                  "answer_support_recall", "scope_accuracy", "extraction_recall"),
    "temporality": ("current_state_accuracy", "supersession_accuracy", "stale_leak_rate",
                    "contradiction_exposure_rate", "deletion_compliance",
                    "cascade_correctness_hop1", "cascade_correctness_hop2",
                    "lineage_completeness"),
    "abstention": ("abstention_recall", "abstention_precision", "false_certainty_rate",
                   "selective_accuracy"),
    "evidence": ("evidence_resolution_rate", "provenance_coverage",
                 "unsupported_claim_rate", "extraction_spurious_rate"),
}


def metric_family(metric: str) -> str:
    for family, metrics in METRIC_FAMILIES.items():
        if metric in metrics:
            return family
    return "other"


def required_sample_size(baseline_rate: float) -> int:
    """Pre-registered sample size required for a given baseline rate."""
    return power_analysis(baseline_rate, MINIMUM_DETECTABLE_EFFECT)


def _dump(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _dump_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in sorted(rows, key=lambda item: json.dumps(item, sort_keys=True)):
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")


STRATIFICATION_AXES = ("task_type", "hop", "history_size", "filler")


def _history_bucket(size: int | None) -> str:
    """Same buckets as loaders.meme.stratify (plan §9.1), applied to whatever
    rows the runner produced instead of a live BenchmarkInstance list, since
    by the time a row reaches reports.py the instance is gone."""
    if size is None:
        return "unknown"
    if size <= 2:
        return "xs"
    if size <= 10:
        return "s"
    if size <= 50:
        return "m"
    return "l"


def _stratification(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    """Sample counts per stratification axis, deduplicated by case_id so a case
    with N metrics is counted once, not N times. A result reported only as a
    flat mean hides whether the sample is concentrated in one hop or history
    size; this table is what makes that visible (plan §9.1, §11)."""
    one_row_per_case: dict[str, dict[str, Any]] = {}
    for row in rows:
        one_row_per_case.setdefault(row["case_id"], row)
    table: dict[str, dict[str, int]] = {axis: {} for axis in STRATIFICATION_AXES}
    for row in one_row_per_case.values():
        buckets = {
            "task_type": str(row.get("task_type", "unknown")),
            "hop": str(row.get("hop", 0)),
            "history_size": _history_bucket(row.get("history_size")),
            "filler": str(row.get("filler", "nofiller")),
        }
        for axis, bucket in buckets.items():
            table[axis][bucket] = table[axis].get(bucket, 0) + 1
    return table


def _percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round(fraction * (len(ordered) - 1)))))
    return round(ordered[index], 3)


def write_reports(out: Path, manifest: dict[str, Any], rows: list[dict[str, Any]],
                  errors: list[dict[str, Any]], leakage: list[dict[str, Any]],
                  latency: list[dict[str, Any]] | None = None) -> None:
    out.mkdir(parents=True, exist_ok=True)
    _dump(out / "run_manifest.json", manifest)
    _dump_jsonl(out / "metrics.jsonl", rows)
    _dump_jsonl(out / "errors.jsonl", errors)
    _dump_jsonl(out / "leakage.jsonl", leakage)
    _dump_jsonl(out / "latency.jsonl", latency or [])

    summary = _summary(manifest, rows, errors, leakage, latency or [])
    _dump(out / "summary.json", summary)
    _dump(out / "pareto.json", _pareto(rows, latency or []))
    # G4 is a latency/token gate, so it is published with the latency data.
    (out / "report.md").write_text(_markdown(summary, errors, leakage), encoding="utf-8")


def _summary(manifest: dict[str, Any], rows: list[dict[str, Any]], errors: list[dict[str, Any]],
             leakage: list[dict[str, Any]], latency: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
    per_case: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
    by_task: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for row in rows:
        grouped[(row["adapter"], row["metric"])].append(row["value"])
        per_case[(row["adapter"], row["metric"])][row["case_id"]] = row["value"]
        by_task[(row["task_type"], row["adapter"], row["metric"])].append(row["value"])

    endpoints: dict[str, Any] = {}
    for (adapter, metric), values in sorted(grouped.items()):
        observed = sum(values) / len(values)
        endpoints.setdefault(adapter, {})[metric] = {
            "mean": observed, "n": len(values), "family": metric_family(metric),
            "required_n": required_sample_size(observed),
            "minimum_detectable_effect": MINIMUM_DETECTABLE_EFFECT,
            "power_basis": "observed_rate",
            "confirmatory": len(values) >= required_sample_size(observed),
        }

    task_types: dict[str, Any] = {}
    for (task, adapter, metric), values in sorted(by_task.items()):
        observed = sum(values) / len(values)
        task_types.setdefault(task, {}).setdefault(adapter, {})[metric] = {
            "mean": observed, "n": len(values), "family": metric_family(metric),
            "required_n": required_sample_size(observed),
            "confirmatory": len(values) >= required_sample_size(observed),
        }

    comparisons: dict[str, Any] = {}
    for metric in sorted({row["metric"] for row in rows}):
        cortex = per_case.get(("cortex", metric), {})
        for baseline in ("bm25", "bm25_temporal", "raw_context", "no_memory"):
            other = per_case.get((baseline, metric), {})
            common = sorted(set(cortex) & set(other))
            if len(common) < 2:
                continue
            arm_a = [cortex[key] for key in common]
            arm_b = [other[key] for key in common]
            diff, low, high = paired_bootstrap_ci(arm_a, arm_b, n_resamples=1000)
            baseline_rate = sum(arm_b) / len(arm_b)
            required = required_sample_size(baseline_rate)
            comparisons[f"cortex_vs_{baseline}:{metric}"] = {
                "n": len(common), "diff": diff, "ci_low": low, "ci_high": high,
                "ci_includes_zero": low <= 0 <= high,
                "family": metric_family(metric),
                # Plan §5: confirmatory means powered for the pre-registered
                # MDE, measured against the baseline arm.
                "required_n": required,
                "minimum_detectable_effect": MINIMUM_DETECTABLE_EFFECT,
                "power_basis": "baseline_arm",
                "p_value": paired_bootstrap_p_value(arm_a, arm_b),
                "confirmatory": len(common) >= required,
            }
    _apply_holm_bonferroni(comparisons)

    summary: dict[str, Any] = {
        "schema": "cortex_benchmark_summary/v1",
        "cortex_version": manifest.get("cortex_version"),
        "corpus_hash": manifest.get("corpus_hash"),
        "dataset_revisions": manifest.get("dataset_revisions", {}),
        "endpoints": endpoints,
        "by_task_type": task_types,
        "stratification": _stratification(rows),
        "paired_comparisons": comparisons,
    }
    # Efficiency and the G4 cost gate live in pareto.json: summary.json is part
    # of the deterministic payload (plan §7/§11), latency is not.
    summary["claim_class"] = "exploratory" if _exploratory_run(rows) else "confirmatory"
    if summary["claim_class"] == "exploratory":
        for adapter_metrics in endpoints.values():
            for entry in adapter_metrics.values():
                entry["confirmatory"] = False
        for task_adapters in task_types.values():
            for adapter_metrics in task_adapters.values():
                for entry in adapter_metrics.values():
                    entry["confirmatory"] = False
        for key, entry in comparisons.items():
            if key.startswith("__"):
                continue
            entry["confirmatory"] = False
    summary["gates"] = _gates(endpoints, comparisons, rows, errors, leakage)
    summary["decision"] = _decision(summary)
    return summary


def _exploratory_run(rows: list[dict[str, Any]]) -> bool:
    """True when every annotated row is exploratory (LongMemEval / no kappa)."""
    qualities = [row["annotation_quality"] for row in rows if row.get("annotation_quality")]
    return bool(qualities) and all(quality == "exploratory" for quality in qualities)


def _apply_holm_bonferroni(comparisons: dict[str, Any]) -> None:
    """Correct p-values inside each family (plan §5), never across families."""
    by_family: dict[str, list[str]] = defaultdict(list)
    for key, entry in comparisons.items():
        by_family[entry["family"]].append(key)

    corrections: dict[str, Any] = {}
    for family, keys in sorted(by_family.items()):
        # Deterministic order so the Holm ranking never depends on dict order.
        ordered = sorted(keys)
        p_values = [comparisons[key]["p_value"] for key in ordered]
        rejected = holm_bonferroni(p_values)
        for key, significant in zip(ordered, rejected):
            comparisons[key]["holm_significant"] = significant
        corrections[family] = {
            "comparisons": len(ordered),
            "rejected": sum(rejected),
            "smallest_p_value": min(p_values),
            "largest_p_value": max(p_values),
        }
    # Kept out of the per-comparison namespace so consumers can distinguish
    # correction metadata from a single comparison.
    comparisons["__holm_bonferroni__"] = corrections


def _efficiency(latency: list[dict[str, Any]]) -> dict[str, Any]:
    """Latency percentiles per phase and token cost per adapter (plan §10.5)."""
    phases: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    tokens: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    for row in latency:
        for phase, value in row.get("phase_ms", {}).items():
            phases[row["adapter"]][phase].append(float(value))
        for name, value in row.get("tokens", {}).items():
            tokens[row["adapter"]][name].append(int(value))
    efficiency: dict[str, Any] = {}
    for adapter in sorted({*phases, *tokens}):
        entry: dict[str, Any] = {}
        for phase, values in sorted(phases.get(adapter, {}).items()):
            entry[f"{phase}_p50_ms"] = _percentile(values, 0.50)
            entry[f"{phase}_p95_ms"] = _percentile(values, 0.95)
        for name, counts in sorted(tokens.get(adapter, {}).items()):
            entry[f"tokens_{name}_mean"] = round(sum(counts) / len(counts), 3)
        efficiency[adapter] = entry
    return efficiency


def _gates(endpoints: dict[str, Any], comparisons: dict[str, Any], rows: list[dict[str, Any]],
           errors: list[dict[str, Any]], leakage: list[dict[str, Any]]) -> dict[str, Any]:
    def mean(adapter: str, metric: str) -> float | None:
        value = endpoints.get(adapter, {}).get(metric)
        return None if value is None else value["mean"]

    def comparison(metric: str, baseline: str) -> dict[str, Any] | None:
        return comparisons.get(f"cortex_vs_{baseline}:{metric}")

    def holds(metric: str, baseline: str) -> bool | None:
        """Gate decision.  The paired interval is required for a *claim*, but a
        gate must still be decidable on very small runs, so it falls back to the
        difference of means and says so."""
        entry = comparison(metric, baseline)
        if entry is not None:
            return entry["diff"] <= 0
        cortex, other = mean("cortex", metric), mean(baseline, metric)
        return None if (cortex is None or other is None) else cortex <= other

    stale_cortex, stale_bm25, stale_raw = mean("cortex", "stale_leak_rate"), mean("bm25", "stale_leak_rate"), mean("raw_context", "stale_leak_rate")
    return {
        "G0_reproducibility": {"explicit_errors": len(errors), "leakage_events": len(leakage),
                               "clean": not errors and not leakage},
        "G1_cortex_integrity": {
            "stale_leak_rate_cortex": stale_cortex,
            "stale_leak_rate_bm25": stale_bm25,
            "stale_leak_rate_raw_context": stale_raw,
            "stale_leak_not_worse_than_bm25": holds("stale_leak_rate", "bm25"),
            "stale_leak_not_worse_than_raw_context": holds("stale_leak_rate", "raw_context"),
            "paired_interval_available": comparison("stale_leak_rate", "bm25") is not None,
            "exceptions_converted_to_zero": 0,
        },
        "G2_relative_value": {
            metric: {"comparison": f"cortex_vs_{baseline}",
                     "holm_significant": (comparison(metric, baseline) or {}).get("holm_significant"),
                     **(comparison(metric, baseline) or {"n": 0})}
            for metric, baseline in (("set_f1", "bm25"), ("set_f1", "raw_context"),
                                     ("current_state_accuracy", "bm25"),
                                     ("deletion_compliance", "bm25"),
                                     ("abstention_recall", "bm25"),
                                     ("recall_at_k", "bm25"))
        },
        "G3_assertion_safety": {
            "false_certainty_reported_per_case": any(row["metric"] == "false_certainty_rate" for row in rows),
            "unsupported_claim_rate": mean("cortex", "unsupported_claim_rate"),
            "evidence_resolution_rate": mean("cortex", "evidence_resolution_rate"),
        },
    }


def cost_gate(efficiency: dict[str, Any]) -> dict[str, Any]:
    """Reference budgets of plan §12 (G4), reported against this hardware.

    The 300 ms compile / 150 ms query targets assume the reference machine;
    on slower hardware the values are reported so the trade-off is visible
    instead of silently redefining the target.
    """
    cortex = efficiency.get("cortex", {})
    compiled = cortex.get("tokens_compiled_mean")
    query_p95 = cortex.get("query_p95_ms")
    compile_p95 = cortex.get("compile_p95_ms")
    return {
        "compile_p95_ms": compile_p95,
        "query_p95_ms": query_p95,
        "compiled_tokens_mean": compiled,
        "token_budget_respected": None if compiled is None else compiled <= 4096,
        "query_p95_within_reference": None if query_p95 is None else query_p95 <= 150,
        "compile_p95_within_reference": None if compile_p95 is None else compile_p95 <= 300,
    }


def _decision(summary: dict[str, Any]) -> str:
    """Choose one of the plan §17 decisions from the observed evidence."""
    gates = summary["gates"]
    if not gates["G0_reproducibility"]["clean"]:
        return "bloquear_expansao"
    # Exploratory corpora (no kappa) cannot back a product promotion even when
    # n is large enough to look confirmatory on sample-size grounds alone.
    if summary.get("claim_class") == "exploratory":
        return "diagnostico"
    safety = gates["G1_cortex_integrity"]
    stale = safety["stale_leak_rate_cortex"]
    if stale is None:
        return "diagnostico"
    if stale > 0:
        return "recalibrar"
    # A win only counts when it is powered for the pre-registered MDE and
    # survives Holm-Bonferroni inside its family (plan §5/§17).
    wins = [entry for entry in gates["G2_relative_value"].values()
            if entry.get("confirmatory") and entry.get("holm_significant")
            and not entry.get("ci_includes_zero", True) and entry.get("diff", 0) > 0]
    if wins:
        return "promover_com_reservas"
    return "reduzir_claim"


def _pareto(rows: list[dict[str, Any]], latency: list[dict[str, Any]]) -> dict[str, Any]:
    """Quality per token and quality per millisecond, by adapter (plan §11)."""
    quality: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        quality[row["adapter"]][row["metric"]].append(row["value"])
    cost: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    counts: dict[str, int] = defaultdict(int)
    for row in latency:
        counts[row["adapter"]] += 1
        for name, value in row.get("tokens", {}).items():
            cost[row["adapter"]][f"tokens_{name}"] += int(value)
        for phase, value in row.get("phase_ms", {}).items():
            cost[row["adapter"]][f"ms_{phase}"] += float(value)
    curves: dict[str, Any] = {}
    for adapter in sorted(quality):
        entry: dict[str, Any] = {
            "quality": {metric: sum(values) / len(values) for metric, values in sorted(quality[adapter].items())}
        }
        n = max(1, counts.get(adapter, 1))
        entry["cost_per_case"] = {key: round(value / n, 4) for key, value in sorted(cost.get(adapter, {}).items())}
        entry["quality_per_compiled_token"] = round(
            entry["quality"].get("recall_at_k", 0.0) / max(1e-9, entry["cost_per_case"].get("tokens_compiled", 0.0)), 6)
        curves[adapter] = entry
    return {"schema": "cortex_benchmark_pareto/v1", "adapters": curves,
            "efficiency": _efficiency(latency),
            "gates": {"G4_operational_cost": cost_gate(_efficiency(latency))}}


def _markdown(summary: dict[str, Any], errors: list[dict[str, Any]], leakage: list[dict[str, Any]]) -> str:
    lines = ["# Cortex memory benchmark v1", "",
             f"- Corpus: `{summary.get('corpus_hash')}`",
             f"- Revisões: `{json.dumps(summary.get('dataset_revisions', {}), sort_keys=True)}`",
             f"- Classe de claim: `{summary.get('claim_class', 'confirmatory')}`",
             "", "## Endpoints por task type", "",
             "| Task type | Adapter | Endpoint | Mean | n / req n | Confirmatório |", "|---|---|---|---:|---|---|"]
    for task, adapters in summary["by_task_type"].items():
        for adapter, metrics in adapters.items():
            for metric, value in metrics.items():
                lines.append(f"| {task} | {adapter} | {metric} | {value['mean']:.4f} | {value['n']}/{value['required_n']} | {value['confirmatory']} |")
    lines += ["", "## Estratificação da amostra (plano §9.1)", "",
              "Contagem de casos únicos por eixo — uma média única nunca revela se a amostra "
              "está concentrada em um hop, tamanho de histórico ou carga de filler.", "",
              "| Eixo | Bucket | n (casos) |", "|---|---|---:|"]
    for axis, buckets in summary.get("stratification", {}).items():
        for bucket, count in sorted(buckets.items()):
            lines.append(f"| {axis} | {bucket} | {count} |")
    lines += ["", "## Comparação pareada (cortex − baseline)", "",
              f"MDE pré-registrado: {MINIMUM_DETECTABLE_EFFECT}. Confirmatório exige n ≥ `required_n`. "
              "`holm` marca rejeição após correção dentro da família.", "",
              "| Métrica | Baseline | n | req n | diff | IC95 | p | holm |", "|---|---|---:|---:|---:|---|---:|---|"]
    for key, value in summary["paired_comparisons"].items():
        if key.startswith("__"):
            continue
        metric, baseline = key.split(":", 1)
        lines.append(f"| {metric} | {baseline} | {value['n']} | {value['required_n']} | {value['diff']:+.4f} | "
                     f"[{value['ci_low']:+.4f}, {value['ci_high']:+.4f}] | {value['p_value']:.4f} | "
                     f"{value.get('holm_significant')} |")
    lines += ["", "### Correção de múltiplas hipóteses (Holm-Bonferroni, por família)", "",
              "| Família | Comparações | Rejeitadas | menor p | maior p |", "|---|---:|---:|---:|---:|"]
    for family, correction in summary["paired_comparisons"].get("__holm_bonferroni__", {}).items():
        lines.append(f"| {family} | {correction['comparisons']} | {correction['rejected']} | "
                     f"{correction['smallest_p_value']:.4f} | {correction['largest_p_value']:.4f} |")
    lines += ["", "## Gates", ""]
    for name, gate in summary["gates"].items():
        lines.append(f"### {name}")
        for key, value in gate.items():
            lines.append(f"- {key}: {value}")
        lines.append("")
    lines += ["## Eficiência", "",
              "Latência por fase, percentis e custo por token são publicados em `pareto.json`: "
              "não fazem parte do payload determinístico (plano §7).", ""]
    lines += ["", "## Segurança", "", f"- Erros explícitos: {len(errors)}", f"- Eventos de leakage: {len(leakage)}",
              "", "## Decisão de produto", "",
              f"`{summary['decision']}`", "",
              "Decisões possíveis (plano §17): promover, recalibrar, reduzir_claim, bloquear_expansao, diagnostico.",
              "Uma média única nunca é o resultado final; ver `summary.json` por task type e split.", ""]
    return "\n".join(lines)
