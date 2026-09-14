from __future__ import annotations

from .base import Adapter, case_events, result_for, token_count


class RawContextAdapter(Adapter):
    name = "raw_context"

    def setup(self, instance):
        super().setup(instance)
        self._instance = instance

    def ingest(self, instance):
        self._events = case_events(instance)

    def query(self, instance):
        budget = instance.constraints.max_context_tokens
        selected = []
        used = 0
        for eid, content, _session_ts, _event_ts in reversed(self._events):
            cost = token_count(content)
            if used + cost > budget:
                break
            selected.append(eid)
            used += cost
        selected.reverse()
        return result_for(instance, self.name, retrieved=selected, selected=selected, evidence=selected,
                          trace={"truncation": "latest_first", "context_tokens": used},
                          tokens={"input": token_count(instance.query.text), "retrieved": used, "compiled": used})
