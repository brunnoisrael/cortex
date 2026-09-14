"""Command-line runner for the reproducible benchmark MVP."""

from __future__ import annotations

import argparse
import json
import time
from datetime import UTC
from pathlib import Path
from typing import Any

from .adapters import BM25Adapter, BM25TemporalAdapter, CortexAdapter, NoMemoryAdapter, OracleAdapter, RawContextAdapter
from .errors import LeakageError
from .manifest import RunManifest, freeze_seed, load_manifest
from .metrics import case_metrics
from .reports import write_reports
from .schema import BenchmarkInstance, Checksums, Gold, instance_from_dict, sha256_prefixed, validate_checksums

ADAPTERS = {"cortex": CortexAdapter, "bm25": BM25Adapter, "bm25_temporal": BM25TemporalAdapter,
            "raw_context": RawContextAdapter, "no_memory": NoMemoryAdapter, "oracle": OracleAdapter}


def load_instances(manifest: RunManifest, manifest_path: Path) -> list[BenchmarkInstance]:
    if manifest.cases is not None:
        raw = manifest.cases
    elif manifest.corpus:
        corpus = Path(manifest.corpus)
        if not corpus.is_absolute():
            corpus = (manifest_path.parent / corpus).resolve()
        raw = [json.loads(line) for line in corpus.read_text(encoding="utf-8").splitlines() if line.strip()]
    else:
        raise ValueError("manifest needs cases or corpus")
    instances = []
    for item in raw:
        item = dict(item)
        # The bundled fixture uses the final recorded session as its cutoff
        # boundary.  Add an empty post-cutoff sentinel so the v1 invariant
        # (cutoff.session_index < len(history)) remains true without making a
        # query session part of the visible history.
        if item.get("cutoff", {}).get("session_index") == len(item.get("history", [])):
            history = list(item["history"])
            last = history[-1]
            from datetime import datetime, timedelta

            last_time = datetime.fromisoformat(last["timestamp"].replace("Z", "+00:00"))
            last_time = (last_time if last_time.tzinfo else last_time.replace(tzinfo=UTC)) + timedelta(days=1)
            history.append({"session_id": "__cutoff__", "timestamp": last_time.isoformat().replace("+00:00", "Z"), "events": []})
            item["history"] = history
        instance = instance_from_dict(item)
        # The checked-in synthetic fixture keeps its checksums readable as
        # placeholders; materialise the exact values before the gate.
        zeros = "sha256:" + "0" * 64
        if instance.checksums.history == zeros or instance.checksums.gold == zeros:
            instance = instance.model_copy(update={"checksums": Checksums(
                history=sha256_prefixed([s.model_dump(by_alias=True, mode="json") for s in instance.history_until_cutoff()]),
                gold=sha256_prefixed(instance.gold.model_dump(mode="json")))})
        instances.append(instance)
    return instances


def guard_case(instance: BenchmarkInstance) -> None:
    if instance.constraints.allowed_future_data is not False:
        raise LeakageError(f"allowed_future_data must be false for {instance.id}")
    cutoff_time = _timestamp(instance.history[instance.cutoff.session_index].timestamp)
    # A corpus may retain post-cutoff sessions for audit, but they are never
    # passed to an adapter.  Inspect the visible prefix for timestamps that
    # jump beyond the cutoff boundary.
    for session in instance.history[:instance.cutoff.session_index]:
        for event in session.events:
            if _timestamp(event.timestamp or session.timestamp) > cutoff_time:
                raise LeakageError(f"future event at {session.session_id} in {instance.id}")
    validate_checksums(instance)


def _timestamp(value: str):
    from datetime import datetime

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return (parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)).astimezone(UTC)


def _safe_instance(instance: BenchmarkInstance) -> BenchmarkInstance:
    # Baselines and Cortex receive the query/history contract, not annotations.
    # Oracle is explicitly the debugging ceiling and is the only exception.
    return instance.model_copy(update={"gold": Gold(answer=None, expected_abstention=False, gold_evidence=[])})


def run_benchmark(manifest_path: Path, adapters: list[str], report_out: Path) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    if manifest.network_enabled:
        raise LeakageError("benchmark gate requires network_enabled=false")
    freeze_seed(manifest.seed)
    instances = load_instances(manifest, manifest_path)
    selected = []
    for name in adapters:
        if name not in ADAPTERS:
            raise ValueError(f"unknown adapter: {name}")
        selected.append(ADAPTERS[name]())
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    leakage: list[dict[str, Any]] = []
    for instance in instances:
        try:
            guard_case(instance)
        except LeakageError as exc:
            event = {"case_id": instance.id, "error": type(exc).__name__, "message": str(exc)}
            leakage.append(event)
            errors.append(event)
            continue
        for adapter in selected:
            started = time.perf_counter()
            try:
                source = instance if adapter.name == "oracle" else _safe_instance(instance)
                result = adapter.run(source)
                metrics = case_metrics(result, instance)
                for metric, value in sorted(metrics.items()):
                    rows.append({"case_id": instance.id, "adapter": adapter.name, "metric": metric, "value": round(value, 8), "task_type": instance.task_type, "split": instance.split})
            except Exception as exc:  # explicit case failure; never a zero
                errors.append({"case_id": instance.id, "adapter": adapter.name, "error": type(exc).__name__, "message": str(exc),
                               "elapsed_ms": round((time.perf_counter() - started) * 1000, 3)})
    write_reports(report_out, manifest.model_dump(by_alias=True, mode="json"), rows, errors, leakage)
    return {"cases": len(instances), "rows": len(rows), "errors": len(errors), "leakage": len(leakage), "report_out": str(report_out)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--adapter", nargs="+", choices=sorted(ADAPTERS), required=True)
    parser.add_argument("--report-out", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(run_benchmark(args.manifest, args.adapter, args.report_out), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
