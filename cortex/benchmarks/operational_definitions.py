"""Single source of truth for subjective safety and evidence definitions."""

from __future__ import annotations

from typing import Any

from .schema import BenchmarkInstance


def _ids(values: list[Any]) -> set[str]:
    result: set[str] = set()
    for value in values:
        if isinstance(value, str):
            result.add(value)
        elif isinstance(value, dict):
            for key in ("id", "entity_id", "evidence_id"):
                if value.get(key):
                    result.add(str(value[key]))
    return result


def _trace_ids(result: Any, *keys: str) -> set[str]:
    trace = getattr(result, "trace", {}) or {}
    found: set[str] = set()
    for key in keys:
        found |= _ids(trace.get(key, []))
    return found


def is_stale_leak(result: Any, instance: BenchmarkInstance) -> bool:
    invalid = set(instance.gold.invalid_entities)
    selected = _ids(getattr(result, "selected", []))
    evidence = _ids(getattr(result, "evidence", []))
    if not invalid:
        return False
    marked_invalid = _trace_ids(result, "invalid_ids", "superseded_ids", "stale_ids", "deleted_ids")
    answer_state = getattr(result, "answer_state", "unknown")
    if answer_state == "current" and invalid & (_ids(getattr(result, "retrieved", [])) | selected):
        return True
    if invalid & selected - marked_invalid:
        return True
    if invalid & evidence - marked_invalid and not _trace_ids(result, "superseded_ids", "invalid_ids"):
        return True
    return False


def is_contradiction_exposure(result: Any, instance: BenchmarkInstance) -> bool:
    selected = _ids(getattr(result, "selected", []))
    resolved = _trace_ids(result, "current_ids", "invalid_ids", "superseded_ids", "resolved_ids")
    state = getattr(result, "answer_state", "unknown")
    return any(a in selected and b in selected and not ({a, b} & resolved) and state == "unknown"
               for a, b in instance.gold.contradiction_pairs)


def count_unsupported_claims(result: Any) -> int:
    evidence = _ids(getattr(result, "evidence", []))
    count = 0
    for item in getattr(result, "selected", []):
        if isinstance(item, dict) and (item.get("claim") or item.get("content")):
            evidence_id = item.get("evidence_id") or item.get("source_id")
            if not evidence_id or evidence_id not in evidence:
                count += 1
    return count


def is_abstention_correct(result: Any, instance: BenchmarkInstance) -> bool:
    abstained = bool(getattr(result, "abstained", False))
    if abstained and not getattr(result, "missing_evidence", []):
        return False
    return abstained == instance.gold.expected_abstention


def is_deletion_compliant(result: Any, instance: BenchmarkInstance) -> bool:
    return not (set(instance.gold.invalid_entities) & _ids(getattr(result, "selected", [])))


def is_cascade_correct(result: Any, instance: BenchmarkInstance, hop: int) -> bool:
    expected = {item for pair in instance.gold.supersession_pairs for item in pair}
    selected = _ids(getattr(result, "selected", []))
    lineage = _trace_ids(result, "lineage_ids", "updated_ids", f"hop{hop}_ids")
    if not lineage:
        lineage = selected
    return expected.issubset(lineage) and not (set(instance.gold.invalid_entities) & selected)
