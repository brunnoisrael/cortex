"""Session and phase reviews (PRD §13)."""

from __future__ import annotations

from cortex.knowledge.models import ArtifactType, Authority, Entity, Provenance, Status
from cortex.storage.store import KnowledgeStore

UNRESOLVED_RE = ("pendente", "unresolved", "ficou faltando", "open question", "todo",
                 "not resolved", "ainda falta")
RISK_RE = ("risco", "risk", "cuidado", "careful")


def build_session_review(store: KnowledgeStore, session_id: str) -> Entity | None:
    """Review artifact summarizing what a session produced (PRD §13.1)."""
    session = store.get_session(session_id)
    if not session:
        return None
    counts: dict[str, int] = {"intentions": 0, "adrs": 0, "fixes": 0, "correndas_proposed": 0}
    unresolved: list[str] = []
    risks: list[str] = []
    produced_ids: list[str] = []

    for ent in store.all_entities():
        if ent.session_id != session_id:
            continue
        produced_ids.append(ent.id)
        if ent.type == ArtifactType.INTENTION:
            counts["intentions"] += 1
        elif ent.type == ArtifactType.ADR:
            counts["adrs"] += 1
        elif ent.type == ArtifactType.FIX:
            counts["fixes"] += 1
            rc = ent.details.get("root_cause", "")
            if rc and not rc.startswith("unknown"):
                risks.append(f"fix in session targets: {ent.details.get('symptom', ent.statement)}")
        elif ent.type == ArtifactType.CORRENDA and ent.status == Status.PROPOSED:
            counts["correndas_proposed"] += 1

    events = store.all_events(session_id)
    for e in events:
        content = (e.get("content") or "").lower()
        if any(m in content for m in UNRESOLVED_RE):
            unresolved.append((e.get("content") or "")[:160])

    eid = store.reserve_entity_id(ArtifactType.REVIEW)
    review = Entity(
        id=eid,
        type=ArtifactType.REVIEW,
        statement=f"Session review: {session_id}",
        status=Status.ACTIVE,
        authority=Authority.OBSERVED,
        confidence=1.0,
        session_id=session_id,
        details={
            "produced": counts,
            "unresolved": unresolved[:5],
            "risks": risks[:5],
            "next_actions": [],
            "open_threads": unresolved[:5],
        },
        provenance=Provenance(
            source_session=session_id,
            source_events=[e["id"] for e in events][:20],
            extraction_source="code_git_evidence",
        ),
    )
    store.upsert(review)
    store.end_session(session_id)
    return review
