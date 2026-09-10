"""Regression tests for the 2026-09-10 external-review fixes.

Each section names the fix it pins; see docs/adr/ for the decisions.
"""

from __future__ import annotations

from pathlib import Path

import cortex.server.mcp_server as mcp_server
from cortex.knowledge.models import Authority, Status
from cortex.storage.store import KnowledgeStore
from cortex.workspace import CORTEX_DIR


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
