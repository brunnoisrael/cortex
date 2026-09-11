"""Deterministic governance policies and review queue helpers."""

from __future__ import annotations

from typing import Any

from cortex.knowledge.models import Authority, Entity, EvidenceStatus, ReviewPolicy, RiskLevel, Status
from cortex.storage.store import KnowledgeStore


def review_queue(store: KnowledgeStore) -> list[Entity]:
    """Return artifacts awaiting a human or evidence-backed decision."""
    return [
        entity for entity in store.all_entities()
        if entity.status in (Status.CANDIDATE, Status.PROPOSED)
        or entity.details.get("contradiction_pending")
        or entity.risk_level == RiskLevel.HIGH
    ]


def promotion_check(store: KnowledgeStore, entity: Entity) -> dict[str, Any]:
    evidence = store.list_evidence(entity.id)
    resolved = [item for item in evidence if item.status == EvidenceStatus.RESOLVED and item.fingerprint]
    policy = entity.review_policy
    if policy == ReviewPolicy.OBSERVE:
        allowed = True
        reason = "observe policy"
    elif policy == ReviewPolicy.MULTIPLE_EVIDENCE:
        allowed = len(resolved) >= 2
        reason = "at least two resolved evidence records" if allowed else "requires at least two resolved evidence records"
    else:
        allowed = False
        reason = "requires explicit human confirmation"
    return {
        "allowed": allowed,
        "reason": reason,
        "policy": policy.value,
        "risk_level": entity.risk_level.value,
        "resolved_evidence": len(resolved),
    }


def promote(
    store: KnowledgeStore,
    entity_id: str,
    *,
    actor: str = "human",
    reason: str = "",
    evidence_ids: list[str] | None = None,
    force_human: bool = False,
) -> Entity:
    entity = store.get(entity_id)
    if entity is None:
        raise ValueError(f"entity {entity_id} not found")
    check = promotion_check(store, entity)
    if not check["allowed"] and not force_human:
        raise ValueError(check["reason"])
    authority = Authority.HUMAN_CONFIRMED if force_human or actor == "human" else Authority.AGENT_INFERRED
    promoted = store.transition(
        entity_id, Status.ACTIVE, action="promote", actor=actor,
        reason=reason or check["reason"], evidence_ids=evidence_ids,
        authority=authority,
    )
    if promoted is None:
        raise ValueError(f"entity {entity_id} not found")
    return promoted


def reject(store: KnowledgeStore, entity_id: str, *, actor: str = "human", reason: str = "") -> Entity:
    entity = store.transition(
        entity_id, Status.REJECTED, action="reject", actor=actor,
        reason=reason or "rejected during review",
    )
    if entity is None:
        raise ValueError(f"entity {entity_id} not found")
    return entity


def quarantine(store: KnowledgeStore, entity_id: str, *, actor: str = "human", reason: str = "") -> Entity:
    entity = store.transition(
        entity_id, Status.QUARANTINED, action="quarantine", actor=actor,
        reason=reason or "quarantined pending review",
    )
    if entity is None:
        raise ValueError(f"entity {entity_id} not found")
    return entity

