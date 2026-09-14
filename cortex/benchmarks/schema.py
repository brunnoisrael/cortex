"""Canonical v1 benchmark schema.

The schema is intentionally independent from Cortex' persisted knowledge
models.  It is the boundary between a corpus and every adapter.
"""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .errors import SchemaError

AnswerState = Literal["current", "superseded", "stale", "deleted", "unknown", "out_of_scope"]
TaskType = Literal["exact_recall", "aggregation", "tracking", "deletion", "cascade", "absence"]
Source = Literal["meme", "swebench", "longmemeval", "internal"]
Split = Literal["dev", "eval", "regression"]

_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


class _BenchmarkModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class Cutoff(_BenchmarkModel):
    session_index: int
    branch: str = "main"
    commit: str | None = None


class Query(_BenchmarkModel):
    text: str
    files: list[str] = Field(default_factory=list)
    symbols: list[str] = Field(default_factory=list)


class Event(_BenchmarkModel):
    role: Literal["user", "assistant", "system", "tool", "commit", "diff", "test"]
    content: str
    timestamp: str | None = None
    # Loaders may preserve source-local identifiers without changing content.
    id: str | None = None


class Session(_BenchmarkModel):
    session_id: str
    timestamp: str
    events: list[Event]


class Gold(_BenchmarkModel):
    answer: str | None
    accepted_answers: list[str] = Field(default_factory=list)
    current_entities: list[str] = Field(default_factory=list)
    invalid_entities: list[str] = Field(default_factory=list)
    expected_abstention: bool
    gold_evidence: list[str]
    supersession_pairs: list[tuple[str, str]] = Field(default_factory=list)
    contradiction_pairs: list[tuple[str, str]] = Field(default_factory=list)
    annotation_agreement: dict[str, Any] | None = None
    annotation_quality: Literal["confirmatory", "exploratory"] = "confirmatory"


class Constraints(_BenchmarkModel):
    max_context_tokens: int = Field(gt=0)
    allowed_future_data: Literal[False] = False


class Checksums(_BenchmarkModel):
    history: str
    gold: str

    @field_validator("history", "gold")
    @classmethod
    def valid_sha256(cls, value: str) -> str:
        if not _SHA256.fullmatch(value):
            raise ValueError("checksum must use sha256:<64 lowercase hex characters>")
        return value


class BenchmarkInstance(_BenchmarkModel):
    schema_: Literal["cortex_memory_benchmark/v1"] = Field("cortex_memory_benchmark/v1", alias="schema")
    id: str
    source: Source
    source_revision: str
    split: Split
    domain: str
    history: list[Session]
    cutoff: Cutoff
    query: Query
    task_type: TaskType
    gold: Gold
    constraints: Constraints
    checksums: Checksums

    @model_validator(mode="after")
    def validate_contract(self) -> BenchmarkInstance:
        if self.cutoff.session_index < 0 or self.cutoff.session_index >= len(self.history):
            raise ValueError("cutoff.session_index must be within history")
        if self.gold.expected_abstention and (self.gold.current_entities or self.gold.answer):
            raise ValueError("an abstention gold cannot contain an answer or current entities")
        if self.task_type == "cascade" and not self.gold.supersession_pairs:
            raise ValueError("cascade cases require supersession_pairs")
        if self.gold.annotation_quality == "exploratory":
            kappa = (self.gold.annotation_agreement or {}).get("kappa")
            if kappa is None:
                raise ValueError("exploratory annotations require annotation_agreement.kappa")
        # Timestamp parsing is strict when a timestamp is supplied, but a
        # future event is left for runner.guard_case: keeping it in the model
        # allows the leakage test to report LeakageError rather than silently
        # dropping the offending event.
        for session in self.history:
            _parse_timestamp(session.timestamp)
            for event in session.events:
                if event.timestamp:
                    _parse_timestamp(event.timestamp)
        return self

    def history_until_cutoff(self) -> list[Session]:
        """Return sessions before the exclusive cutoff boundary.

        ``session_index`` is a boundary, not a count of arbitrary events.  A
        corpus must retain at least one session so index 0 is a valid empty
        history case only when represented by a synthetic pre-cutoff session.
        """
        return self.history[: self.cutoff.session_index]

    def canonical_history(self) -> bytes:
        return canonical_json([session.model_dump(by_alias=True, mode="json") for session in self.history_until_cutoff()])

    def canonical_gold(self) -> bytes:
        return canonical_json(self.gold.model_dump(mode="json"))


def _parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def canonical_json(value: Any) -> bytes:
    import json

    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_prefixed(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value)).hexdigest()


def validate_checksums(instance: BenchmarkInstance) -> None:
    if sha256_prefixed([s.model_dump(by_alias=True, mode="json") for s in instance.history_until_cutoff()]) != instance.checksums.history:
        raise SchemaError(f"history checksum mismatch for {instance.id}")
    if sha256_prefixed(instance.gold.model_dump(mode="json")) != instance.checksums.gold:
        raise SchemaError(f"gold checksum mismatch for {instance.id}")


def instance_from_dict(raw: dict[str, Any]) -> BenchmarkInstance:
    try:
        return BenchmarkInstance.model_validate(raw)
    except Exception as exc:
        raise SchemaError(str(exc)) from exc
