"""Adapter-neutral contract for benchmark v1."""

from __future__ import annotations

import re
import time
from abc import ABC, abstractmethod
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ..schema import AnswerState, BenchmarkInstance


class AdapterResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    schema_: str = Field("cortex_benchmark_result/v1", alias="schema")
    case_id: str
    adapter: str
    status: Literal["ok", "error", "timeout", "abstained"] = "ok"
    retrieved: list[str] = Field(default_factory=list)
    selected: list[str] = Field(default_factory=list)
    answer_state: AnswerState = "unknown"
    abstained: bool = False
    abstention_reason: str | None = None
    missing_evidence: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    answer: str | None = None
    claims: list[dict[str, Any]] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    trace: dict[str, Any] = Field(default_factory=dict)
    latency_ms: dict[str, float] = Field(default_factory=dict)
    tokens: dict[str, int] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


class Adapter(ABC):
    name: str

    def __init__(self) -> None:
        self._instance_id: str | None = None
        self._events: list[tuple[str, str, str, str | None]] = []

    @abstractmethod
    def setup(self, instance: BenchmarkInstance) -> None:
        self._instance_id = instance.id
        self._events = []

    @abstractmethod
    def ingest(self, instance: BenchmarkInstance) -> None:
        """Ingest only the history visible at the cutoff."""

    @abstractmethod
    def query(self, instance: BenchmarkInstance) -> AdapterResult:
        """Return a complete, serialisable result envelope."""

    def teardown(self) -> None:
        """Release per-case state.  Stores are ephemeral and never shared."""

    def run(self, instance: BenchmarkInstance) -> AdapterResult:
        started = time.perf_counter()
        try:
            self.setup(instance)
            ingest_start = time.perf_counter()
            self.ingest(instance)
            ingest_ms = (time.perf_counter() - ingest_start) * 1000
            result = self.query(instance)
        finally:
            self.teardown()
        result.latency_ms.setdefault("ingest", round(ingest_ms, 3))
        result.latency_ms.setdefault("query", round((time.perf_counter() - ingest_start) * 1000, 3))
        result.latency_ms.setdefault("compile", result.latency_ms.get("query", 0.0))
        result.trace.setdefault("total_ms", round((time.perf_counter() - started) * 1000, 3))
        return result


def event_id(session_id: str, event_index: int) -> str:
    return f"{session_id}:{event_index}"


def case_events(instance: BenchmarkInstance) -> list[tuple[str, str, str, str | None]]:
    events = []
    for session in instance.history_until_cutoff():
        for index, event in enumerate(session.events):
            events.append((event_id(session.session_id, index), event.content, session.timestamp, event.timestamp))
    return events


def tokenize(text: str) -> list[str]:
    return re.findall(r"[\wÀ-ÿ]+", text.casefold())


def token_count(text: str) -> int:
    return len(tokenize(text))


def result_for(instance: BenchmarkInstance, adapter: str, **kwargs: Any) -> AdapterResult:
    return AdapterResult(case_id=instance.id, adapter=adapter, **kwargs)
