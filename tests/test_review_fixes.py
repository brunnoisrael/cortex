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
