"""Correnda Commons (Onda 10) — Local-first opt-in pattern generalization & exchange."""

from __future__ import annotations

from typing import Any

from cortex.knowledge.models import (
    ArtifactType,
    Authority,
    Entity,
    Provenance,
    Status,
    session_id_for,
)
from cortex.privacy import redact_sensitive_content
from cortex.storage.store import KnowledgeStore


def export_common_pattern(store: KnowledgeStore, entity_id: str) -> dict[str, Any]:
    """Generalize a human-confirmed local Correnda or ADR for sharing (Onda 10).
    
    Strictly local-first: redacts sensitive data (tokens, paths, keys) and produces
    a clean, project-agnostic engineering pattern schema.
    """
    ent = store.get(entity_id)
    if not ent:
        raise ValueError(f"Entity {entity_id} not found in store")
        
    redacted_statement = redact_sensitive_content(ent.statement)
    
    generalized_scope = []
    for s in ent.scope:
        parts = s.replace("\\", "/").split("/")
        fname = parts[-1] if len(parts) > 1 else s
        # Remove vendor/provider prefixes from filenames (e.g. stripe_webhook -> webhook)
        for prefix in ("stripe_", "github_", "aws_", "postgres_", "mongo_"):
            if fname.lower().startswith(prefix):
                fname = fname[len(prefix):]
        generalized_scope.append(fname)
            
    pattern = {
        "cortex_schema": "correnda_commons/v1",
        "original_id": ent.id,
        "type": ent.type.value,
        "statement": redacted_statement,
        "generalized_scope": list(set(generalized_scope)),
        "rationale": redact_sensitive_content(str(ent.details.get("rationale") or ent.details.get("context") or "")),
        "confidence": round(min(ent.confidence, 0.85), 2),
    }
    return pattern


def import_common_pattern(store: KnowledgeStore, pattern_data: dict[str, Any]) -> Entity:
    """Import a Correnda Commons pattern into the local store as a proposed rule (Onda 10).
    
    Crítico 2 Fix: All external imported knowledge starts as PROPOSED status (never ACTIVE)
    and requires human confirmation before promotion to Tier 1 authority.
    """
    if pattern_data.get("cortex_schema") != "correnda_commons/v1":
        raise ValueError("Invalid pattern schema. Must be 'correnda_commons/v1'")

    kind_str = pattern_data.get("type", "correnda")
    etype = ArtifactType(kind_str)
    eid = store.reserve_entity_id(etype)
    
    ent = Entity(
        id=eid,
        type=etype,
        statement=pattern_data["statement"],
        status=Status.PROPOSED,
        authority=Authority.AGENT_INFERRED,
        confidence=float(pattern_data.get("confidence", 0.70)),
        scope=pattern_data.get("generalized_scope", []),
        session_id=session_id_for("commons"),
        details={
            "rule": pattern_data["statement"],
            "origin": ["correnda_commons"],
            "rationale": pattern_data.get("rationale", ""),
            "imported_from": pattern_data.get("original_id", "commons"),
            "confirmed_by_human": False,
        },
        provenance=Provenance(extraction_source="correnda_commons_import"),
    )
    store.upsert(ent)
    return ent
