"""Engineering knowledge model (PRD §9-17, §45-48).

Five primary artifacts: Intention, ADR, Fix, Correnda, Review —
plus a first-class NegativeKnowledge artifact (§45).
"""

from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ArtifactType(str, Enum):
    INTENTION = "intention"
    ADR = "adr"
    FIX = "fix"
    CORRENDA = "correnda"
    REVIEW = "review"
    NEGATIVE_KNOWLEDGE = "negative_knowledge"
    IDEA = "idea"


class Status(str, Enum):
    CANDIDATE = "candidate"
    PROPOSED = "proposed"
    ACTIVE = "active"
    VALIDATED = "validated"
    IMPLEMENTED = "implemented"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    DEPRECATED = "deprecated"


class Authority(str, Enum):
    OBSERVED = "observed"
    AGENT_INFERRED = "agent_inferred"
    REPOSITORY_VERIFIED = "repository_verified"
    HUMAN_CONFIRMED = "human_confirmed"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"


# Context authority tiers (PRD §48): higher tier = more authoritative source.
AUTHORITY_WEIGHT = {
    Authority.OBSERVED: 0.65,
    Authority.AGENT_INFERRED: 0.70,
    Authority.REPOSITORY_VERIFIED: 0.95,
    Authority.HUMAN_CONFIRMED: 1.0,
}

# Confidence source hierarchy (PRD §8.3).
CONFIDENCE_BY_SOURCE = {
    "explicit_user_statement": 0.95,
    "explicit_agent_statement": 0.85,
    "code_git_evidence": 0.80,
    "high_confidence_pattern": 0.75,
    "llm_inference": 0.65,
    "heuristic_inference": 0.65,
}

RELATIONS = (
    "DECIDED_BASED_ON",
    "IMPLEMENTS",
    "GENERATED",
    "CONFIRMS",
    "CONTRADICTS",
    "SUPERSEDES",
    "REFERENCED_IN",
    "SCOPED_TO",
    "EVIDENCED_BY",
    "OCCURRED_IN",
    "AFFECTS",
    "BLOCKS",
    "RESOLVES",
)


class Provenance(BaseModel):
    source_session: str | None = None
    source_events: list[str] = Field(default_factory=list)
    source_files: list[str] = Field(default_factory=list)
    source_commits: list[str] = Field(default_factory=list)
    source_entities: list[str] = Field(default_factory=list)
    generated_at: str = Field(default_factory=lambda: _utcnow())
    extraction_source: str = "heuristic_inference"


class Freshness(BaseModel):
    last_verified_at: str | None = None
    verification_source: str | None = None
    stale_after_days: int = 90
    stale: bool = False


class Entity(BaseModel):
    """Common envelope for all knowledge artifacts."""

    id: str
    type: ArtifactType
    statement: str
    status: Status = Status.CANDIDATE
    authority: Authority = Authority.AGENT_INFERRED
    confidence: float = 0.6
    scope: list[str] = Field(default_factory=list)
    phase: str | None = None
    session_id: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    provenance: Provenance = Field(default_factory=Provenance)
    freshness: Freshness = Field(default_factory=Freshness)
    superseded_by: str | None = None
    created_at: str = Field(default_factory=lambda: _utcnow())
    updated_at: str = Field(default_factory=lambda: _utcnow())

    @property
    def is_current(self) -> bool:
        """Only current truth enters default context (PRD §17)."""
        return self.status not in (
            Status.SUPERSEDED,
            Status.DEPRECATED,
            Status.REJECTED,
        )


# ---- typed payloads stored inside Entity.details ----

IntentionDetails = dict  # motivation: str, scope paths
FixDetails = dict  # symptom, root_cause, resolution, affected_files, tests
ADRDetails = dict  # context, decision, alternatives_rejected, consequences
CorrendaDetails = dict  # rule, origin fix ids, confirmed_by_human


def _utcnow() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def session_id_for(host: str) -> str:
    return f"sess-{host[:4].lower()}-{uuid.uuid4().hex[:6]}"
