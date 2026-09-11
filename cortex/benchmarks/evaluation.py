"""Reproducible, adapter-neutral retrieval evaluation.

The benchmark separates extraction, ranking and final-context measurements. It
does not claim that external products are installed; adapters can return a
structured ``unavailable`` result instead of silently comparing unlike data.
"""

from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from cortex.compiler.compiler import CompileInput, rank, token_estimate
from cortex.storage.store import KnowledgeStore


@dataclass(frozen=True)
class BenchmarkCase:
    id: str
    query: str
    relevant: tuple[str, ...]
    files: tuple[str, ...] = ()


class RetrievalAdapter(Protocol):
    name: str

    def retrieve(self, case: BenchmarkCase, k: int) -> list[str]: ...


def load_corpus(path: Path) -> list[BenchmarkCase]:
    cases = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        raw = json.loads(line)
        cases.append(BenchmarkCase(
            id=raw["id"], query=raw["query"],
            relevant=tuple(raw.get("relevant", [])), files=tuple(raw.get("files", [])),
        ))
    return cases


def recall_at_k(retrieved: list[str], relevant: tuple[str, ...], k: int) -> float:
    expected = set(relevant)
    return len(expected.intersection(retrieved[:k])) / max(1, len(expected))


def precision_at_k(retrieved: list[str], relevant: tuple[str, ...], k: int) -> float:
    return len(set(retrieved[:k]).intersection(relevant)) / max(1, min(k, len(retrieved)))


def reciprocal_rank(retrieved: list[str], relevant: tuple[str, ...]) -> float:
    expected = set(relevant)
    for index, item in enumerate(retrieved, 1):
        if item in expected:
            return 1 / index
    return 0.0


def ndcg(retrieved: list[str], relevant: tuple[str, ...], k: int) -> float:
    expected = set(relevant)
    dcg = sum((1 / math.log2(index + 2)) for index, item in enumerate(retrieved[:k]) if item in expected)
    ideal = sum(1 / math.log2(index + 2) for index in range(min(k, len(expected))))
    return dcg / ideal if ideal else 0.0


def evaluate_cortex(store: KnowledgeStore, cases: list[BenchmarkCase], k: int = 5) -> dict[str, Any]:
    rows = []
    started = time.perf_counter()
    for case in cases:
        query_started = time.perf_counter()
        items = rank(store, CompileInput(query=case.query, files=list(case.files)), limit=k)
        ids = [item.entity.id for item in items]
        rows.append({
            "id": case.id,
            "retrieved": ids,
            "recall@k": recall_at_k(ids, case.relevant, k),
            "precision@k": precision_at_k(ids, case.relevant, k),
            "mrr": reciprocal_rank(ids, case.relevant),
            "ndcg@k": ndcg(ids, case.relevant, k),
            "query_ms": round((time.perf_counter() - query_started) * 1000, 3),
            "tokens_injected": sum(token_estimate(item.entity.statement) for item in items),
        })
    count = max(1, len(rows))
    return {
        "schema": "cortex_benchmark/v1",
        "adapter": "cortex",
        "cases": len(rows),
        "k": k,
        "metrics": {key: round(sum(row[key] for row in rows) / count, 4)
                    for key in ("recall@k", "precision@k", "mrr", "ndcg@k", "query_ms", "tokens_injected")},
        "rows": rows,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
        "limitations": ["relevance labels are corpus-specific", "external adapters are not bundled"],
    }

