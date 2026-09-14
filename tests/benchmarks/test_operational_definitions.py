from cortex.benchmarks.adapters.base import AdapterResult
from cortex.benchmarks.operational_definitions import (
    is_abstention_correct,
    is_contradiction_exposure,
    is_deletion_compliant,
    is_stale_leak,
)

from .helpers import make_case


def test_stale_leak_positive_negative_and_retrieval_only():
    case = make_case(invalid=["old"])
    assert is_stale_leak(AdapterResult(case_id="case", adapter="x", answer_state="current", selected=["old"]), case)
    assert not is_stale_leak(AdapterResult(case_id="case", adapter="x", retrieved=["old"]), case)
    assert not is_stale_leak(AdapterResult(case_id="case", adapter="x", selected=["new"], trace={"invalid_ids": ["old"]}), case)


def test_abstention_and_deletion_edges():
    case = make_case(abstain=True)
    assert is_abstention_correct(AdapterResult(case_id="case", adapter="x", status="abstained", abstained=True, missing_evidence=["q"]), case)
    assert not is_abstention_correct(AdapterResult(case_id="case", adapter="x", status="abstained", abstained=True), case)
    assert is_deletion_compliant(AdapterResult(case_id="case", adapter="x", selected=[]), make_case(invalid=["old"]))


def test_contradiction_requires_unresolved_pair():
    case = make_case()
    case.gold.contradiction_pairs = [("a", "b")]
    result = AdapterResult(case_id="case", adapter="x", selected=["a", "b"], answer_state="unknown")
    assert is_contradiction_exposure(result, case)
    result.trace["current_ids"] = ["a"]
    assert not is_contradiction_exposure(result, case)
