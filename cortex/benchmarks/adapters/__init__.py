"""Versioned benchmark adapters plus compatibility exports for the old API."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .base import Adapter, AdapterResult
from .bm25 import BM25Adapter
from .bm25_temporal import BM25TemporalAdapter
from .cortex import CortexAdapter
from .no_memory import NoMemoryAdapter
from .oracle import OracleAdapter
from .raw_context import RawContextAdapter
from .vector_rag import VectorRAGAdapter


@dataclass
class LegacyAdapterResult:
    name: str
    available: bool
    metrics: dict[str, Any] | None = None
    limitation: str | None = None


class EvaluationAdapter:
    """Compatibility facade retained for tests and the legacy CLI."""

    name = "adapter"

    def evaluate(self, cases: list[Any], k: int = 5) -> LegacyAdapterResult:
        raise NotImplementedError


class ExternalMemoryAdapter(EvaluationAdapter):
    def __init__(self, name: str, retrieve_fn: Callable[[Any, int], list[str]] | None = None):
        self.name, self.retrieve_fn = name, retrieve_fn

    def evaluate(self, cases: list[Any], k: int = 5) -> LegacyAdapterResult:
        if self.retrieve_fn is None:
            return LegacyAdapterResult(self.name, False, limitation="integration not installed")
        from cortex.benchmarks.evaluation import ndcg, precision_at_k, recall_at_k, reciprocal_rank

        rows = []
        for case in cases:
            ids = self.retrieve_fn(case, k)
            rows.append({"id": case.id, "retrieved": ids,
                         "recall@k": recall_at_k(ids, case.relevant, k),
                         "precision@k": precision_at_k(ids, case.relevant, k),
                         "mrr": reciprocal_rank(ids, case.relevant), "ndcg@k": ndcg(ids, case.relevant, k)})
        n = max(1, len(rows))
        metrics = {key: sum(row[key] for row in rows) / n for key in ("recall@k", "precision@k", "mrr", "ndcg@k")}
        return LegacyAdapterResult(self.name, True, {"adapter": self.name, "cases": len(rows), "metrics": metrics, "rows": rows})


def default_adapters(store: Any) -> dict[str, EvaluationAdapter]:
    """Legacy registry; new runs use the seven v1 adapters directly."""
    from .cortex import LegacyCortexAdapter

    return {
        "cortex": LegacyCortexAdapter(store),
        "agent_memory_engine": ExternalMemoryAdapter("agent_memory_engine"),
        "agent_memory_bridge": ExternalMemoryAdapter("agent_memory_bridge"),
        "basic_memory": ExternalMemoryAdapter("basic_memory"),
        "native_host": ExternalMemoryAdapter("native_host"),
    }


__all__ = ["Adapter", "AdapterResult", "BM25Adapter", "BM25TemporalAdapter", "CortexAdapter",
           "NoMemoryAdapter", "OracleAdapter", "RawContextAdapter", "VectorRAGAdapter", "default_adapters"]
