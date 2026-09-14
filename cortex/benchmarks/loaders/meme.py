from __future__ import annotations

import json
from pathlib import Path

from ..schema import BenchmarkInstance, instance_from_dict


def load_meme(path: Path, *, split: str | None = None, domain: str = "software_project") -> list[BenchmarkInstance]:
    """Load the original local JSON/JSONL representation without rewriting history."""
    raw = json.loads(path.read_text(encoding="utf-8")) if path.suffix == ".json" else [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if isinstance(raw, dict):
        raw = raw.get("data", raw.get("instances", []))
    result = []
    for item in raw:
        if item.get("domain", domain) != domain or (split and item.get("split") != split):
            continue
        normalized = dict(item)
        normalized.setdefault("source", "meme")
        normalized.setdefault("source_revision", "local")
        normalized.setdefault("split", split or "dev")
        normalized.setdefault("domain", domain)
        normalized.setdefault("metadata", {})["transform"] = "meme/local-json-preserved"
        result.append(instance_from_dict(normalized))
    return result
