"""Regression tests for the 2026-09-10 external-review fixes.

Each section names the fix it pins; see docs/adr/ for the decisions.
"""

from __future__ import annotations

from pathlib import Path

import cortex.server.mcp_server as mcp_server
from cortex.distillation.extractors import extract_decisions, extract_negative_knowledge
from cortex.knowledge.models import ArtifactType, Authority, Status
from cortex.storage.store import KnowledgeStore
from cortex.workspace import CORTEX_DIR


def _ev(content: str) -> dict:
    return {"id": "evt-t1", "type": "user_instruction", "session_id": "s1",
            "content": content, "files": []}


# ---------- extraction: negation-first decision detection ----------

def test_negated_decision_is_negative_knowledge_not_adr():
    events = [_ev("Não vamos usar DynamoDB neste domínio")]
    assert extract_decisions(events) == [], (
        "'não vamos usar X' asserts the rejection of X — must not become an ADR"
    )
    negs = extract_negative_knowledge(events)
    assert len(negs) == 1
    assert negs[0].etype == ArtifactType.NEGATIVE_KNOWLEDGE
    assert "DynamoDB" in negs[0].statement


def test_negated_decision_english_variant():
    events = [_ev("We decided not to use MongoDB because the schema is predictable")]
    assert extract_decisions(events) == []
    assert len(extract_negative_knowledge(events)) == 1


def test_affirmative_decision_still_extracts():
    events = [_ev("Vamos usar MySQL 8 porque simplicidade")]
    adrs = extract_decisions(events)
    assert len(adrs) == 1 and adrs[0].etype == ArtifactType.ADR


# ---------- performance: incremental contradiction pass ----------

def test_contradiction_pass_does_not_recount_stable_pairs(store):
    """The contradiction pass is incremental: a pair already carrying a
    CONTRADICTS edge must not be re-counted on every subsequent run
    (the old O(N^2) pass inflated the report counter forever)."""
    from cortex.distillation.engine import DistillationEngine, DistillationReport

    e1 = _mk_entity(store, "adr-0001", "Usar PostgreSQL como banco primário", "src/db")
    e2 = _mk_entity(store, "adr-0002", "Não usar PostgreSQL, migrar para MongoDB", "src/db")
    store.add_edge(e2.id, "CONTRADICTS", e1.id)

    engine = DistillationEngine(store)
    rep1 = DistillationReport()
    engine._detect_contradictions(rep1)
    assert rep1.contradictions == 0, "already-recorded pair must not be re-counted"

    # A new, unrelated entity arrives: only it is re-checked, and the report
    # reflects only genuinely new contradictions.
    _mk_entity(store, "int-0001", "Isolar auth via middleware", "src/auth")
    rep2 = DistillationReport()
    engine._detect_contradictions(rep2)
    assert rep2.contradictions == 0
    assert len(store.edges_of(rel="CONTRADICTS")) == 1


def _mk_entity(store: KnowledgeStore, eid: str, statement: str, scope: str):
    from cortex.knowledge.models import ArtifactType, Entity, Provenance
    ent = Entity(id=eid, type=ArtifactType.ADR, statement=statement,
                 status=Status.ACTIVE, authority=Authority.AGENT_INFERRED,
                 confidence=0.8, scope=[scope],
                 details={"decision": statement},
                 provenance=Provenance(source_session="sess-t"))
    store.upsert(ent)
    return ent


# ---------- governance: cortex_remember authority escalation ----------

def test_cortex_remember_is_agent_inferred_and_proposed(project, monkeypatch):
    """An MCP tool call is agent-mediated: it must never mint
    HUMAN_CONFIRMED/ACTIVE knowledge, or any agent could out-rank every
    human-confirmed rule in the ranking."""
    monkeypatch.setenv("CORTEX_ROOT", str(project))
    mcp_server._stores.clear()
    try:
        result = mcp_server.cortex_remember(
            statement="Validar payload externo antes do destructuring", kind="correnda")
        assert "recorded" in result
        with KnowledgeStore(project / CORTEX_DIR / "cortex.db") as st:
            ents = st.all_entities()
            assert len(ents) == 1
            e = ents[0]
            assert e.authority == Authority.AGENT_INFERRED
            assert e.status == Status.PROPOSED
            assert e.details.get("confirmed_by_human") is False
            assert e.confidence <= 0.85
    finally:
        mcp_server._stores.clear()


def test_cortex_remember_promotion_still_possible_via_cli(project, monkeypatch):
    """The human path still works: set_status via governance raises authority."""
    monkeypatch.setenv("CORTEX_ROOT", str(project))
    mcp_server._stores.clear()
    try:
        result = mcp_server.cortex_remember(statement="usar PostgreSQL", kind="adr")
        eid = result.split()[1]
        with KnowledgeStore(project / CORTEX_DIR / "cortex.db") as st:
            st.set_status(eid, Status.ACTIVE, authority=Authority.HUMAN_CONFIRMED)
            e = st.get(eid)
        assert e.authority == Authority.HUMAN_CONFIRMED
        assert e.status == Status.ACTIVE
    finally:
        mcp_server._stores.clear()
