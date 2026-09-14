from __future__ import annotations

from datetime import UTC, datetime

from .base import Adapter, case_events, result_for, token_count, tokenize


class BM25TemporalAdapter(Adapter):
    """BM25 plus a freshness window: items older than the window are dropped.

    The window is measured backwards from the cutoff (plan §6).  The default
    covers a 30-day horizon, which is the strongest temporal claim a session
    history of this size can support without discarding the whole history.
    """

    name = "bm25_temporal"

    DEFAULT_FRESHNESS_WINDOW_SECONDS = 30 * 24 * 60 * 60

    def __init__(self, freshness_window_seconds: int = DEFAULT_FRESHNESS_WINDOW_SECONDS):
        super().__init__()
        self.freshness_window_seconds = freshness_window_seconds

    def setup(self, instance):
        super().setup(instance)
        self._cutoff_ts = instance.history[instance.cutoff.session_index].timestamp

    def ingest(self, instance):
        self._events = case_events(instance)

    def query(self, instance):
        query_tokens = set(tokenize(instance.query.text))
        cutoff = _dt(self._cutoff_ts)
        scored = []
        for order, (eid, content, session_ts, event_ts) in enumerate(self._events):
            ts = _dt(event_ts or session_ts)
            if (cutoff - ts).total_seconds() > self.freshness_window_seconds:
                continue
            overlap = len(query_tokens & set(tokenize(content)))
            if overlap:
                scored.append((overlap + 1 / (order + 1), eid, content))
        scored.sort(key=lambda row: (-row[0], row[1]))
        top = [row[1] for row in scored[:5]]
        return result_for(instance, self.name, retrieved=top, selected=top, evidence=top,
                          trace={"freshness_window_seconds": self.freshness_window_seconds},
                          tokens={"input": token_count(instance.query.text), "retrieved": sum(token_count(row[2]) for row in scored[:5]), "compiled": 0})


def _dt(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return (parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)).astimezone(UTC)
