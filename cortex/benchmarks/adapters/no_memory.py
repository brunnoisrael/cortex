from __future__ import annotations

from .base import Adapter, result_for, token_count


class NoMemoryAdapter(Adapter):
    name = "no_memory"

    def setup(self, instance):
        super().setup(instance)
        self._query_tokens = set(instance.query.text.casefold().split())

    def ingest(self, instance):
        self._events = []

    def query(self, instance):
        query = instance.query.text
        return result_for(instance, self.name, status="abstained", abstained=True,
                          abstention_reason="no_memory", missing_evidence=[query],
                          trace={"source": "query_only"}, tokens={"input": token_count(query), "retrieved": 0, "compiled": 0})
