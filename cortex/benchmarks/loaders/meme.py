from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..schema import BenchmarkInstance, instance_from_dict

# Stratification axes of plan §9.1: sampling must be reported per task type,
# hop, history size and filler load instead of a single flat average.
STRATIFICATION_AXES = ("task_type", "hop", "history_size", "filler")


def load_meme(path: Path, *, split: str | None = None, domain: str = "software_project",
              limit: int | None = None) -> list[BenchmarkInstance]:
    """Load the original local MEME JSON/JSONL without rewriting history.

    The transcript is preserved verbatim; anything the loader adds (source
    identity, split, provenance of the transform) goes to ``metadata``.  Cases
    from another domain are skipped, never silently converted.
    """
    raw = json.loads(path.read_text(encoding="utf-8")) if path.suffix == ".json" else [
        json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    if isinstance(raw, dict):
        raw = raw.get("data", raw.get("instances", []))
    result: list[BenchmarkInstance] = []
    for item in raw:
        if item.get("domain", domain) != domain or (split and item.get("split") != split):
            continue
        normalized = _normalize(item, split)
        result.append(instance_from_dict(normalized))
        if limit is not None and len(result) >= limit:
            break
    return result


def stratify(instances: list[BenchmarkInstance]) -> dict[str, dict[str, int]]:
    """Count the sample per stratification axis so the report can disclose it."""
    table: dict[str, dict[str, int]] = {axis: {} for axis in STRATIFICATION_AXES}
    for instance in instances:
        metadata = instance.metadata or {}
        buckets = {
            "task_type": instance.task_type,
            "hop": str(metadata.get("hop", 0)),
            "history_size": _history_bucket(len(instance.history)),
            "filler": str(metadata.get("filler", "nofiller")),
        }
        for axis, bucket in buckets.items():
            table[axis][bucket] = table[axis].get(bucket, 0) + 1
    return table


def _history_bucket(size: int) -> str:
    if size <= 2:
        return "xs"
    if size <= 10:
        return "s"
    if size <= 50:
        return "m"
    return "l"


def _normalize(item: dict[str, Any], split: str | None) -> dict[str, Any]:
    normalized = dict(item)
    normalized.setdefault("source", "meme")
    normalized.setdefault("source_revision", "local")
    normalized.setdefault("split", split or "dev")
    normalized.setdefault("domain", "software_project")
    metadata = normalized.get("metadata") if isinstance(normalized.get("metadata"), dict) else {}
    normalized["metadata"] = {**metadata, "transform": "meme/local-json-preserved"}
    return normalized
