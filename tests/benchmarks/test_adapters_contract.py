from cortex.benchmarks.adapters import (
    BM25Adapter,
    BM25TemporalAdapter,
    CortexAdapter,
    NoMemoryAdapter,
    OracleAdapter,
    RawContextAdapter,
)

from .helpers import make_case


def test_all_six_adapters_return_v1_envelope():
    case = make_case()
    for adapter in (CortexAdapter(), BM25Adapter(), BM25TemporalAdapter(), RawContextAdapter(), NoMemoryAdapter(), OracleAdapter()):
        result = adapter.run(case)
        assert result.schema_ == "cortex_benchmark_result/v1"
        assert result.case_id == case.id
        assert result.status in {"ok", "abstained", "error", "timeout"}
        assert set(result.tokens) >= {"input", "retrieved", "compiled"}


def test_cortex_ablation_flags_are_isolated():
    adapter = CortexAdapter(disable_dense=True)
    result = adapter.run(make_case())
    assert result.trace["flags"]["disable_dense"] is True
    assert sum(result.trace["flags"].values()) == 1
