"""Command-line runner for the reproducible benchmark MVP."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import UTC
from pathlib import Path
from typing import Any

from .adapters import BM25Adapter, BM25TemporalAdapter, CortexAdapter, NoMemoryAdapter, OracleAdapter, RawContextAdapter
from .adapters.base import Adapter
from .errors import LeakageError
from .manifest import (
    RunManifest,
    assert_declared_revisions,
    assert_endpoint_table,
    freeze_corpus,
    freeze_seed,
    load_manifest,
    select_split,
)
from .metrics import case_metrics
from .reports import write_reports
from .schema import BenchmarkInstance, Gold, instance_from_dict, validate_checksums

ADAPTERS = {"cortex": CortexAdapter, "bm25": BM25Adapter, "bm25_temporal": BM25TemporalAdapter,
            "raw_context": RawContextAdapter, "no_memory": NoMemoryAdapter, "oracle": OracleAdapter}


def corpus_path(manifest: RunManifest, manifest_path: Path) -> Path | None:
    """Resolve the corpus file the manifest points at, if any."""
    if not manifest.corpus:
        return None
    corpus = Path(manifest.corpus)
    return corpus if corpus.is_absolute() else (manifest_path.parent / corpus).resolve()


def load_instances(manifest: RunManifest, manifest_path: Path) -> list[BenchmarkInstance]:
    """Load and validate every case.  A malformed case aborts the run."""
    if manifest.cases is not None:
        raw = manifest.cases
    elif manifest.corpus:
        corpus = corpus_path(manifest, manifest_path)
        assert corpus is not None
        raw = [json.loads(line) for line in corpus.read_text(encoding="utf-8").splitlines() if line.strip()]
    else:
        raise ValueError("manifest needs cases or corpus")
    if not raw:
        raise ValueError("manifest resolved to an empty corpus")
    return [instance_from_dict(dict(item)) for item in raw]


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


def _adapter_suite(adapters: list[str], ablations: bool) -> list[tuple[str, Adapter]]:
    """The adapters to run, plus one Cortex variant per ablation flag."""
    selected: list[tuple[str, Adapter]] = []
    for name in adapters:
        if name not in ADAPTERS:
            raise ValueError(f"unknown adapter: {name}")
        selected.append((name, ADAPTERS[name]()))
    if ablations:
        for flag in CortexAdapter.ABLATION_FLAGS:
            selected.append((f"cortex[{flag}]", CortexAdapter(**{flag: True})))
    return selected


def run_benchmark(manifest_path: Path, adapters: list[str], report_out: Path,
                  splits: list[str] | None = None, ablations: bool = False) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    if manifest.network_enabled:
        raise LeakageError("benchmark gate requires network_enabled=false")
    assert_endpoint_table(manifest)
    freeze_seed(manifest.seed)
    instances = select_split(load_instances(manifest, manifest_path), splits or manifest.splits)
    assert_declared_revisions(manifest, instances)
    frozen = freeze_corpus(instances)
    pinned = manifest.corpus_hash
    if pinned.startswith("sha256:") and pinned != "sha256:" + "0" * 64:
        corpus = corpus_path(manifest, manifest_path)
        if corpus is not None:
            observed = "sha256:" + hashlib.sha256(corpus.read_bytes()).hexdigest()
            if pinned != observed:
                raise LeakageError(
                    f"corpus hash drift: manifest pins {pinned}, corpus file hashes {observed}"
                )
    manifest = manifest.model_copy(update={"frozen": frozen})
    rows: list[dict[str, Any]] = []
    latency: list[dict[str, Any]] = []
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
        for label, adapter in _adapter_suite(adapters, ablations):
            started = time.perf_counter()
            try:
                # Oracle is the debugging ceiling and the only adapter that may
                # see gold; every other adapter gets the observable contract.
                source = instance if adapter.name == "oracle" else _safe_instance(instance)
                result = adapter.run(source)
                metrics = case_metrics(result, instance)
                # Stratification axes of plan §9.1 (hop, history size, filler
                # load) travel with every row so reports.py can break the
                # aggregate down instead of publishing a single mean.
                for metric, value in sorted(metrics.items()):
                    rows.append({"case_id": instance.id, "adapter": label, "metric": metric,
                                 "value": round(value, 8), "task_type": instance.task_type,
                                 "split": instance.split,
                                 "hop": instance.metadata.get("hop", 0),
                                 "history_size": len(instance.history),
                                 "filler": instance.metadata.get("filler", "nofiller")})
                latency.append({"case_id": instance.id, "adapter": label,
                                "phase_ms": {key: round(value, 3) for key, value in sorted(result.latency_ms.items())},
                                "tokens": dict(sorted(result.tokens.items()))})
            except Exception as exc:  # explicit case failure; never a zero
                errors.append({"case_id": instance.id, "adapter": label, "error": type(exc).__name__, "message": str(exc),
                               "elapsed_ms": round((time.perf_counter() - started) * 1000, 3)})
    write_reports(report_out, manifest.model_dump(by_alias=True, mode="json"), rows, errors, leakage, latency)
    return {"cases": len(instances), "rows": len(rows), "errors": len(errors), "leakage": len(leakage),
            "corpus_hash": frozen.corpus_hash, "report_out": str(report_out)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--adapter", nargs="+", choices=sorted(ADAPTERS), required=True)
    parser.add_argument("--report-out", type=Path, required=True)
    parser.add_argument("--split", nargs="+", choices=["dev", "eval", "regression"], default=None)
    parser.add_argument("--ablation", action="store_true",
                        help="also run the Cortex once per ablation flag (plan §6/§Onda 3)")
    args = parser.parse_args(argv)
    summary = run_benchmark(args.manifest, args.adapter, args.report_out, splits=args.split,
                            ablations=args.ablation)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
