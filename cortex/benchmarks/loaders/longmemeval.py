from __future__ import annotations

import json
from pathlib import Path

from ..schema import BenchmarkInstance, instance_from_dict


def load_longmemeval(path: Path, *, split: str = "dev") -> list[BenchmarkInstance]:
    """Normalize local LongMemEval rows as a secondary external control.

    Onda 4 keeps this dataset out of the release gate: without a human
    annotation agreement every case is loaded as ``exploratory``, so it can
    never back a confirmatory claim, and the transform is recorded in
    ``metadata`` rather than rewritten into history.
    """
    rows = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(rows, dict):
        rows = rows.get("data", rows.get("instances", []))
    result: list[BenchmarkInstance] = []
    for row in rows:
        raw = dict(row)
        gold = dict(raw.get("gold") or {})
        gold.setdefault("answer", None)
        gold.setdefault("expected_abstention", False)
        gold.setdefault("gold_evidence", [])
        agreement = gold.get("annotation_agreement")
        gold["annotation_quality"] = "confirmatory" if (agreement or {}).get("kappa") else "exploratory"
        if gold["annotation_quality"] == "exploratory":
            gold["annotation_agreement"] = agreement or {"kappa": 0.0}
        raw["gold"] = gold
        raw.setdefault("source", "longmemeval")
        raw.setdefault("source_revision", "local")
        raw.setdefault("split", split)
        raw.setdefault("domain", raw.get("domain", "general"))
        raw.setdefault("metadata", {})
        raw["metadata"] = {
            **(raw["metadata"] if isinstance(raw["metadata"], dict) else {}),
            "transform": "longmemeval/local-json-normalized",
            "external_control": True,
        }
        result.append(instance_from_dict(raw))
    return result
