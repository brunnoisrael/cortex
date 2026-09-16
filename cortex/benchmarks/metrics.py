"""Deterministic per-case metrics for benchmark v1."""

from __future__ import annotations

import math
from collections.abc import Iterable

from .adapters.base import AdapterResult
from .operational_definitions import (
    count_unsupported_claims,
    is_abstention_correct,
    is_cascade_correct,
    is_contradiction_exposure,
    is_deletion_compliant,
    is_stale_leak,
)
from .schema import BenchmarkInstance


def _gold(instance: BenchmarkInstance) -> list[str]:
    return instance.gold.current_entities or instance.gold.gold_evidence


def _session_grain(value: str) -> str:
    return value.split(":", 1)[0]


def _project_ids(ids: list[str], instance: BenchmarkInstance) -> list[str]:
    """Collapse ``session:event`` IDs to session IDs when the gold is session-grained.

    LongMemEval's cleaned files only name the sessions that contain the answer.
    Adapters still retrieve event IDs.  Without this projection every LME
    retrieval score would be identically zero even when the right session was
    retrieved.
    """
    if instance.metadata.get("evidence_grain") != "session":
        return ids
    projected: list[str] = []
    seen: set[str] = set()
    for item in ids:
        grain = _session_grain(item)
        if grain not in seen:
            seen.add(grain)
            projected.append(grain)
    return projected


def _project_result(result: AdapterResult, instance: BenchmarkInstance) -> AdapterResult:
    if instance.metadata.get("evidence_grain") != "session":
        return result
    trace = dict(result.trace)
    if "extracted_ids" in trace:
        trace["extracted_ids"] = _project_ids(list(trace["extracted_ids"]), instance)
    return result.model_copy(
        update={
            "retrieved": _project_ids(result.retrieved, instance),
            "selected": _project_ids(result.selected, instance),
            "evidence": _project_ids(result.evidence, instance),
            "trace": trace,
        }
    )


def recall_at_k(retrieved: list[str], gold: Iterable[str], k: int) -> float:
    expected = set(gold)
    return len(expected & set(retrieved[:k])) / len(expected) if expected else 0.0


def precision_at_k(retrieved: list[str], gold: Iterable[str], k: int) -> float:
    top = retrieved[:k]
    return len(set(top) & set(gold)) / len(top) if top else 0.0


def mrr(retrieved: list[str], gold: Iterable[str]) -> float:
    expected = set(gold)
    return next((1 / index for index, item in enumerate(retrieved, 1) if item in expected), 0.0)


def ndcg_at_k(retrieved: list[str], gold: Iterable[str], k: int) -> float:
    expected = set(gold)
    dcg = sum(1 / math.log2(index + 2) for index, item in enumerate(retrieved[:k]) if item in expected)
    ideal = sum(1 / math.log2(index + 2) for index in range(min(k, len(expected))))
    return dcg / ideal if ideal else 0.0


def set_f1(result: AdapterResult, instance: BenchmarkInstance) -> float:
    """Endpoint primário de ``aggregation`` (plano §4): F1 sobre o conjunto."""
    expected, selected = set(_gold(instance)), set(result.selected)
    if not expected and not selected:
        return 1.0
    if not expected or not selected:
        return 0.0
    overlap = len(expected & selected)
    precision, recall = overlap / len(selected), overlap / len(expected)
    return 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0


def answer_support_recall(result: AdapterResult, instance: BenchmarkInstance) -> float:
    return recall_at_k(result.evidence, instance.gold.gold_evidence, len(result.evidence))


def _extracted_ids(result: AdapterResult) -> set[str]:
    return set(result.trace.get("extracted_ids", []))


def extraction_recall(result: AdapterResult, instance: BenchmarkInstance) -> float:
    """Share of gold evidence that distillation ever turned into knowledge.

    Mede extração isolada do ranking: um item pode estar destilado e ainda
    assim não ser recuperado para a query.
    """
    gold = set(instance.gold.gold_evidence)
    return len(gold & _extracted_ids(result)) / len(gold) if gold else 1.0


def extraction_spurious_rate(result: AdapterResult, instance: BenchmarkInstance) -> float:
    """Share of distilled items that are not gold evidence for this case."""
    extracted = _extracted_ids(result)
    if not extracted:
        return 0.0
    return len(extracted - set(instance.gold.gold_evidence)) / len(extracted)


def scope_accuracy(result: AdapterResult, instance: BenchmarkInstance) -> float:
    expected, selected = set(instance.gold.current_entities), set(result.selected)
    return float(expected == selected) if expected else float(not selected)


def current_state_accuracy(result, instance) -> float:
    return float(set(result.selected) & set(instance.gold.current_entities) == set(instance.gold.current_entities))


def supersession_accuracy(result, instance) -> float:
    invalid = set(instance.gold.invalid_entities)
    return float(not (invalid & set(result.selected)))


def stale_leak_rate(result, instance) -> float:
    return float(is_stale_leak(result, instance))


def contradiction_exposure_rate(result, instance) -> float:
    return float(is_contradiction_exposure(result, instance))


def deletion_compliance(result, instance) -> float:
    return float(is_deletion_compliant(result, instance))


def cascade_correctness(result, instance, hop: int) -> float:
    return float(is_cascade_correct(result, instance, hop))


def abstention_precision(result, instance) -> float:
    pred = result.abstained
    return float(not pred or instance.gold.expected_abstention)


def abstention_recall(result, instance) -> float:
    return float(is_abstention_correct(result, instance))


def false_certainty_rate(result, instance) -> float:
    return float(not instance.gold.expected_abstention and result.abstained is False and not result.evidence)


def selective_accuracy(result, instance) -> float:
    return float(result.abstained or bool(set(result.selected) & set(_gold(instance))))


def risk_coverage_curve(results: list[AdapterResult], instances: list[BenchmarkInstance]) -> list[tuple[float, float]]:
    pairs = sorted(zip(results, instances), key=lambda pair: (pair[0].abstained, pair[0].case_id))
    curve = []
    for count in range(1, len(pairs) + 1):
        covered = pairs[:count]
        risk = sum(1 - selective_accuracy(result, instance) for result, instance in covered) / count
        curve.append((count / len(pairs), risk))
    return curve


def evidence_resolution_rate(result, instance) -> float:
    if not result.selected:
        return 1.0
    return sum(1 for item in result.selected if item in result.evidence) / len(result.selected)


def provenance_coverage(result, instance) -> float:
    return len(set(result.evidence) & set(instance.gold.gold_evidence)) / len(instance.gold.gold_evidence) if instance.gold.gold_evidence else 1.0


def lineage_completeness(result, instance) -> float:
    expected = {item for pair in instance.gold.supersession_pairs for item in pair}
    return len(expected & set(result.trace.get("lineage_ids", result.selected))) / len(expected) if expected else 1.0


def explanation_faithfulness(result, instance, counterfactual_results) -> float:
    return float(set(result.evidence) != set(counterfactual_results.evidence))


def unsupported_claim_rate(result, instance) -> float:
    return count_unsupported_claims(result) / len(result.selected) if result.selected else 0.0


def case_metrics(result: AdapterResult, instance: BenchmarkInstance, k: int = 5) -> dict[str, float]:
    result = _project_result(result, instance)
    gold = _gold(instance)
    values = {"recall_at_k": recall_at_k(result.retrieved, gold, k),
              "precision_at_k": precision_at_k(result.retrieved, gold, k),
              "mrr": mrr(result.retrieved, gold), "ndcg_at_k": ndcg_at_k(result.retrieved, gold, k),
              "evidence_resolution_rate": evidence_resolution_rate(result, instance),
              "stale_leak_rate": stale_leak_rate(result, instance),
              "contradiction_exposure_rate": contradiction_exposure_rate(result, instance),
              "deletion_compliance": deletion_compliance(result, instance),
              "abstention_recall": abstention_recall(result, instance),
              "false_certainty_rate": false_certainty_rate(result, instance),
              "unsupported_claim_rate": unsupported_claim_rate(result, instance),
              "lineage_completeness": lineage_completeness(result, instance),
              "set_f1": set_f1(result, instance),
              "scope_accuracy": scope_accuracy(result, instance),
              "current_state_accuracy": current_state_accuracy(result, instance),
              "supersession_accuracy": supersession_accuracy(result, instance),
              "answer_support_recall": answer_support_recall(result, instance),
              "provenance_coverage": provenance_coverage(result, instance)}
    # Extraction is measured only where the adapter reports what distillation
    # produced; for the baselines it is not applicable, never a zero.
    if "extracted_ids" in result.trace:
        values["extraction_recall"] = extraction_recall(result, instance)
        values["extraction_spurious_rate"] = extraction_spurious_rate(result, instance)
    if instance.task_type == "cascade":
        values["cascade_correctness_hop1"] = cascade_correctness(result, instance, 1)
        values["cascade_correctness_hop2"] = cascade_correctness(result, instance, 2)
    return values
