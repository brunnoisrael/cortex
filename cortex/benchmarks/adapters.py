"""Optional evaluation adapters.

No competing memory product is imported or contacted by default. Adapters
report availability explicitly, so a missing host is not scored as zero.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from cortex.benchmarks.evaluation import BenchmarkCase, evaluate_cortex
from cortex.storage.store import KnowledgeStore


@dataclass
class AdapterResult:
    name: str
    available: bool
    metrics: dict[str, Any] | None = None
    limitation: str | None = None


class EvaluationAdapter:
    name = "adapter"

    def evaluate(self, cases: list[BenchmarkCase], k: int = 5) -> AdapterResult:
        raise NotImplementedError


class CortexAdapter(EvaluationAdapter):
    name = "cortex"

    def __init__(self, store: KnowledgeStore):
        self.store = store

    def evaluate(self, cases: list[BenchmarkCase], k: int = 5) -> AdapterResult:
        return AdapterResult(self.name, True, evaluate_cortex(self.store, cases, k=k))


class ExternalMemoryAdapter(EvaluationAdapter):
    """Adapter contract for an installed external memory engine.

    ``retrieve_fn`` is injected by an integration package or test harness;
    Cortex never invents external scores when it is absent.
    """

    def __init__(self, name: str, retrieve_fn: Callable[[BenchmarkCase, int], list[str]] | None = None):
        self.name = name
        self.retrieve_fn = retrieve_fn

    def evaluate(self, cases: list[BenchmarkCase], k: int = 5) -> AdapterResult:
        if self.retrieve_fn is None:
            return AdapterResult(self.name, False, limitation="integration not installed")
        rows = []
        from cortex.benchmarks.evaluation import ndcg, precision_at_k, recall_at_k, reciprocal_rank
        for case in cases:
            ids = self.retrieve_fn(case, k)
            rows.append({
                "id": case.id, "retrieved": ids,
                "recall@k": recall_at_k(ids, case.relevant, k),
                "precision@k": precision_at_k(ids, case.relevant, k),
                "mrr": reciprocal_rank(ids, case.relevant), "ndcg@k": ndcg(ids, case.relevant, k),
            })
        count = max(1, len(rows))
        metrics = {key: sum(row[key] for row in rows) / count
                   for key in ("recall@k", "precision@k", "mrr", "ndcg@k")}
        return AdapterResult(self.name, True, {"adapter": self.name, "cases": len(rows), "metrics": metrics, "rows": rows})


def default_adapters(store: KnowledgeStore) -> dict[str, EvaluationAdapter]:
    """Registry required by the comparative benchmark contract."""
    return {
        "cortex": CortexAdapter(store),
        "agent_memory_engine": ExternalMemoryAdapter("agent_memory_engine"),
        "agent_memory_bridge": ExternalMemoryAdapter("agent_memory_bridge"),
        "basic_memory": ExternalMemoryAdapter("basic_memory"),
        "native_host": ExternalMemoryAdapter("native_host"),
    }


def load_huggingface_dataset(dataset_id: str, *, config: str | None = None, split: str = "train") -> list[dict[str, Any]]:
    """Opt-in loader for a local/cache Hugging Face dataset."""
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise RuntimeError("install the optional `datasets` package to use Hugging Face benchmarks") from exc
    dataset = load_dataset(dataset_id, config, split=split) if config else load_dataset(dataset_id, split=split)
    return [dict(row) for row in dataset]


def adapter_availability() -> dict[str, bool]:
    """Cheap diagnostics for optional command-based integrations."""
    return {
        "agent_memory_engine": bool(shutil.which("agent-memory-engine")),
        "agent_memory_bridge": bool(shutil.which("agent-memory-bridge")),
        "basic_memory": bool(shutil.which("basic-memory")),
    }
