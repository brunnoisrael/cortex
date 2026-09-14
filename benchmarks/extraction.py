"""Corpus-based extraction evaluation with per-artifact metrics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cortex.distillation.extractors import (
    extract_decisions,
    extract_fixes,
    extract_intentions,
    extract_negative_knowledge,
)


EXTRACTORS = (extract_decisions, extract_intentions, extract_negative_knowledge, extract_fixes)


def load_extraction_corpus(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def evaluate_extraction(cases: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    totals: dict[str, dict[str, int]] = {}
    for case in cases:
        events = case.get("events", [])
        predictions = [candidate for extractor in EXTRACTORS for candidate in extractor(events)]
        expected = case.get("expected", [])
        matched: set[int] = set()
        true_positive = 0
        for candidate in predictions:
            found = next((index for index, item in enumerate(expected) if index not in matched
                          and item.get("type") == candidate.etype.value
                          and item.get("contains", "").casefold() in candidate.statement.casefold()), None)
            if found is not None:
                matched.add(found)
                true_positive += 1
        by_type = {artifact: {"tp": 0, "predicted": 0, "expected": 0}
                   for artifact in {item.get("type") for item in expected}}
        for item in expected:
            by_type.setdefault(item.get("type"), {"tp": 0, "predicted": 0, "expected": 0})["expected"] += 1
        for candidate in predictions:
            by_type.setdefault(candidate.etype.value, {"tp": 0, "predicted": 0, "expected": 0})["predicted"] += 1
        for index in matched:
            by_type[expected[index]["type"]]["tp"] += 1
        for artifact, values in by_type.items():
            total = totals.setdefault(artifact, {"tp": 0, "predicted": 0, "expected": 0})
            for key in total:
                total[key] += values[key]
        rows.append({"id": case.get("id"), "predicted": len(predictions), "expected": len(expected),
                     "true_positive": true_positive, "false_positive": len(predictions) - true_positive,
                     "false_negative": len(expected) - true_positive, "by_artifact": by_type})
    metrics = {}
    for artifact, values in totals.items():
        metrics[artifact] = {
            "precision": values["tp"] / max(1, values["predicted"]),
            "recall": values["tp"] / max(1, values["expected"]),
            "false_positive": values["predicted"] - values["tp"],
        }
    return {"schema": "extraction_benchmark/v1", "cases": len(cases), "metrics": metrics, "rows": rows}

