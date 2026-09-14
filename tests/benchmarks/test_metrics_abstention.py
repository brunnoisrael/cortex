from cortex.benchmarks.adapters.base import AdapterResult
from cortex.benchmarks.metrics import abstention_recall, false_certainty_rate

from .helpers import make_case


def test_abstention_is_not_silently_zero():
    case = make_case(abstain=True)
    result = AdapterResult(case_id=case.id, adapter="x", status="abstained", abstained=True, missing_evidence=["x"])
    assert abstention_recall(result, case) == 1.0
    assert false_certainty_rate(result, case) == 0.0
