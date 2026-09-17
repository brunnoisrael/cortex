"""Standard Dense Vector RAG baseline adapter for benchmark v1.

Simulates the industry-standard conversational RAG pipeline:
- No epistemic authority modeling
- No temporal supersession / invalidation policy
- No Evidence Ledger or AST verification
- Dense semantic similarity retrieval over raw session chunks
"""

from __future__ import annotations

from cortex.distillation.extractors import dense_semantic_similarity

from .base import Adapter, case_events, result_for, token_count


class VectorRAGAdapter(Adapter):
    name = "vector_rag"

    def setup(self, instance):
        super().setup(instance)

    def ingest(self, instance):
        self._events = case_events(instance)

    def query(self, instance):
        query_text = instance.query.text
        scored = []
        for eid, content, _session_ts, _event_ts in self._events:
            sim = dense_semantic_similarity(query_text, content)
            if sim > 0.0:
                scored.append((sim, eid, content))

        # Sort strictly by dense semantic similarity descending
        scored.sort(key=lambda row: (-row[0], row[1]))
        top = [row[1] for row in scored[:5]]

        return result_for(
            instance,
            self.name,
            retrieved=top,
            selected=top,
            evidence=top,
            trace={
                "scores": {eid: round(score, 6) for score, eid, _ in scored[:5]},
                "pipeline": ["dense_similarity", "top_k"],
                "authority_filter": False,
                "supersession_filter": False,
                "evidence_ledger": False,
            },
            tokens={
                "input": token_count(instance.query.text),
                "retrieved": sum(token_count(row[2]) for row in scored[:5]),
                "compiled": 0,
            },
        )
