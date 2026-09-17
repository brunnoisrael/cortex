"""Append-only, versionable provenance records for benchmark executions.

The deterministic report artifacts deliberately exclude wall-clock and host data.
This module records that operational provenance separately, one JSON object per
completed invocation, so a published result can be traced to its code, inputs,
configuration and generated artifacts without weakening gate G0.
"""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .schema import BenchmarkInstance


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _git_metadata(repository_root: Path) -> dict[str, Any]:
    """Return the exact source revision, preserving unavailable state honestly."""
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repository_root, check=True,
            capture_output=True, text=True,
        ).stdout.strip()
        dirty = bool(subprocess.run(
            ["git", "status", "--porcelain"], cwd=repository_root, check=True,
            capture_output=True, text=True,
        ).stdout.strip())
    except (OSError, subprocess.CalledProcessError):
        return {"commit": None, "dirty": None}
    return {"commit": commit or None, "dirty": dirty}


def _context_budget(instances: list[BenchmarkInstance]) -> dict[str, Any]:
    values = sorted({item.constraints.max_context_tokens for item in instances})
    return {"values": values, "minimum": min(values), "maximum": max(values)}


def build_experiment_record(
    *,
    manifest_path: Path,
    manifest: dict[str, Any],
    adapters: list[str],
    instances: list[BenchmarkInstance],
    report_out: Path,
    errors: int,
    leakage: int,
    repository_root: Path | None = None,
    recorded_at: datetime | None = None,
) -> dict[str, Any]:
    """Build a complete execution record from immutable inputs and outputs."""
    root = repository_root or Path.cwd()
    when = recorded_at or datetime.now(UTC)
    frozen = manifest.get("frozen") or {}
    artifacts = {
        name: _sha256(report_out / name)
        for name in ("run_manifest.json", "metrics.jsonl", "summary.json", "errors.jsonl",
                     "leakage.jsonl", "pareto.json", "report.md")
    }
    summary = json.loads((report_out / "summary.json").read_text(encoding="utf-8"))
    return {
        "schema": "cortex_benchmark_experiment/v1",
        "recorded_at": when.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "source": _git_metadata(root),
        "manifest": {"path": str(manifest_path), "sha256": _sha256(manifest_path)},
        "corpus": {
            "declared_hash": manifest["corpus_hash"],
            "frozen_hash": frozen.get("corpus_hash"),
            "dataset_revisions": manifest.get("dataset_revisions", {}),
        },
        "adapters": adapters,
        "models": {
            "embedding": {"name": manifest["embedding_model"], "version": manifest["embedding_version"]},
            "reader": "none (retrieval-only benchmark)",
        },
        "tokenizer": manifest["tokenizer"],
        "context_budget": _context_budget(instances),
        "environment": {
            "declared_hardware": manifest["hardware"],
            "declared_os": manifest["os"],
            "declared_python": manifest["python_version"],
            "runtime_hardware": platform.machine() or None,
            "runtime_os": platform.platform() or None,
            "runtime_python": platform.python_version(),
        },
        "classification": manifest["evidence_classification"],
        "outcome": {"errors": errors, "leakage": leakage, "decision": summary.get("decision")},
        "artifacts": artifacts,
    }


def append_experiment_record(registry_path: Path, record: dict[str, Any]) -> None:
    """Append exactly one canonical JSONL record for a completed execution."""
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    with registry_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
