from cortex.benchmarks.adapters.base import AdapterResult
from cortex.benchmarks.metrics import deletion_compliance, recall_at_k, stale_leak_rate

from .helpers import make_case


def test_temporal_metrics():
    case = make_case(invalid=["old"])
    assert recall_at_k(["s0:0"], ["s0:0"], 1) == 1.0
    assert stale_leak_rate(AdapterResult(case_id="case", adapter="x", selected=["old"], answer_state="current"), case) == 1.0
    assert deletion_compliance(AdapterResult(case_id="case", adapter="x", selected=[]), case) == 1.0
