import pytest

from cortex.benchmarks.schema import BenchmarkInstance

from .helpers import make_case


def test_schema_validates_and_uses_alias():
    case = make_case()
    assert case.schema_ == "cortex_memory_benchmark/v1"
    assert case.history_until_cutoff()[0].session_id == "s0"


@pytest.mark.parametrize("patch", [{"cutoff": {"session_index": 9}}, {"gold": {"expected_abstention": True, "answer": "x"}}])
def test_schema_rejects_invariants(patch):
    case = make_case().model_dump(by_alias=True)
    case.update(patch)
    with pytest.raises(Exception):
        BenchmarkInstance.model_validate(case)
