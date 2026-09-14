from __future__ import annotations

from .base import Adapter, case_events, result_for, token_count, tokenize


class BM25Adapter(Adapter):
    name = "bm25"

    def setup(self, instance):
        super().setup(instance)

    def ingest(self, instance):
        self._events = case_events(instance)

    def query(self, instance):
        query_tokens = set(tokenize(instance.query.text))
        scored = []
        for order, (eid, content, _session_ts, _event_ts) in enumerate(self._events):
            words = tokenize(content)
            overlap = len(query_tokens & set(words))
            # Deterministic BM25-like lexical score; no validity filtering.
            score = overlap / (1 + len(words) * 0.01) + (1 / (order + 1) if overlap else 0)
            if score:
                scored.append((score, eid, content))
        scored.sort(key=lambda row: (-row[0], row[1]))
        top = [row[1] for row in scored[:5]]
        return result_for(instance, self.name, retrieved=top, selected=top, evidence=top,
                          trace={"scores": {eid: round(score, 8) for score, eid, _ in scored[:5]}, "validity_filter": False},
                          tokens={"input": token_count(instance.query.text), "retrieved": sum(token_count(row[2]) for row in scored[:5]), "compiled": 0})
