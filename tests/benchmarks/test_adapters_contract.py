from cortex.benchmarks.adapters import (
    BM25Adapter,
    BM25TemporalAdapter,
    CortexAdapter,
    NoMemoryAdapter,
    OracleAdapter,
    RawContextAdapter,
    VectorRAGAdapter,
)

from .helpers import make_case


def test_all_seven_adapters_return_v1_envelope():
    case = make_case()
    for adapter in (
        CortexAdapter(),
        BM25Adapter(),
        BM25TemporalAdapter(),
        RawContextAdapter(),
        VectorRAGAdapter(),
        NoMemoryAdapter(),
        OracleAdapter(),
    ):
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


def test_vector_rag_ranks_dense_matches_and_exposes_baseline_limits():
    case = make_case(
        query="qual banco usar para transações",
        history=[
            {
                "session_id": "s0",
                "timestamp": "2026-01-01T00:00:00Z",
                "events": [
                    {"role": "user", "content": "O banco para transações é PostgreSQL.",
                     "timestamp": "2026-01-01T00:01:00Z"},
                    {"role": "user", "content": "A interface web usa React.",
                     "timestamp": "2026-01-01T00:02:00Z"},
                ],
            },
            {"session_id": "s1", "timestamp": "2026-01-02T00:00:00Z", "events": []},
        ],
    )
    result = VectorRAGAdapter().run(case)

    assert result.retrieved == result.selected == result.evidence
    assert result.retrieved[0] == "s0:0"
    assert result.trace["pipeline"] == ["fixed_local_encoder", "cosine_similarity", "top_k"]
    assert result.trace["encoder"] == "hash-ngrams/v1"
    assert result.trace["authority_filter"] is False
    assert result.trace["supersession_filter"] is False
    assert result.trace["evidence_ledger"] is False


def test_vector_rag_uses_deterministic_tie_breaking_and_ignores_zero_scores():
    case = make_case(
        query="PostgreSQL",
        history=[
            {
                "session_id": "s0",
                "timestamp": "2026-01-01T00:00:00Z",
                "events": [
                    {"role": "user", "content": "PostgreSQL", "timestamp": "2026-01-01T00:01:00Z"},
                    {"role": "user", "content": "PostgreSQL", "timestamp": "2026-01-01T00:02:00Z"},
                    {"role": "user", "content": "Redis", "timestamp": "2026-01-01T00:03:00Z"},
                ],
            },
            {"session_id": "s1", "timestamp": "2026-01-02T00:00:00Z", "events": []},
        ],
    )
    result = VectorRAGAdapter().run(case)

    assert result.retrieved == ["s0:0", "s0:1"]
    assert set(result.trace["scores"]) == {"s0:0", "s0:1"}
