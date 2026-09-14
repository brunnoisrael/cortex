from __future__ import annotations

import json
from pathlib import Path

from ..schema import BenchmarkInstance, instance_from_dict


def load_longmemeval(path: Path) -> list[BenchmarkInstance]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(rows, dict):
        rows = rows.get("data", rows.get("instances", []))
    result = []
    for row in rows:
        raw = dict(row)
        raw.setdefault("source", "longmemeval")
        raw.setdefault("source_revision", "local")
        raw.setdefault("split", "dev")
        raw.setdefault("domain", "general")
        raw.setdefault("gold", {}).setdefault("answer", None)
        raw["gold"].setdefault("expected_abstention", False)
        raw["gold"].setdefault("gold_evidence", [])
        raw.setdefault("gold", {}).setdefault("annotation_quality", "exploratory")
        raw.setdefault("gold", {}).setdefault("annotation_agreement", {"kappa": 0.0})
        result.append(instance_from_dict(raw))
    return result
