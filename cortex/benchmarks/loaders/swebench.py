from __future__ import annotations

import json
from pathlib import Path

from ..errors import LeakageError
from ..schema import BenchmarkInstance, Gold, instance_from_dict


def load_swebench(path: Path, *, split: str = "dev") -> list[BenchmarkInstance]:
    """Normalize local SWE-bench metadata; patch fields never enter history."""
    rows = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(rows, dict):
        rows = rows.get("data", rows.get("instances", []))
    result = []
    for row in rows:
        if "patch" not in row or "test_patch" not in row:
            raise LeakageError("SWE-bench row is missing patch/test_patch, cannot prove exclusion")
        raw = dict(row.get("normalized", row))
        raw.pop("patch", None)
        raw.pop("test_patch", None)
        raw.setdefault("gold", {})["answer"] = row["patch"]
        raw["gold"].setdefault("gold_evidence", row.get("gold_evidence", []))
        raw.setdefault("source", "swebench")
        raw.setdefault("source_revision", str(row.get("base_commit", "local")))
        raw.setdefault("split", split)
        raw.setdefault("domain", "software_project")
        instance = instance_from_dict(raw)
        serialized = instance.model_copy(update={"gold": Gold(answer=None, expected_abstention=False, gold_evidence=[])}).model_dump_json()
        if row["patch"] in serialized or row["test_patch"] in serialized:
            raise LeakageError(f"patch leaked into normalized SWE-bench instance {instance.id}")
        result.append(instance)
    return result
