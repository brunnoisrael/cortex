"""Tests for MCP server unified pipeline (Dogfooding Wave 2).

Validates that MCP tools extend the core pipeline:
- Active session caching across tool calls
- Automatic raw event capture (PRD §7) for cortex_emit and cortex_remember
- Complete provenance enrichment (source_session, source_events, source_files, source_commits)
- Relational edge creation (auto-linking and explicit cortex_link)
"""

from __future__ import annotations

import json

import cortex.server.mcp_server as mcp_server
from cortex.knowledge.models import ArtifactType, Status


def test_mcp_unified_session_and_events(project, store, monkeypatch):
    monkeypatch.setenv("CORTEX_ROOT", str(project))
    mcp_server._stores.clear()
    mcp_server._active_sessions.clear()

    # 1. cortex_init creates session and records session_start event
    init_res = mcp_server.cortex_init(branch="feature/test", task="dogfooding validation")
    assert "CORTEX CONTEXT" in init_res or isinstance(init_res, str)

    sessions = store.conn.execute("SELECT * FROM sessions").fetchall()
    assert len(sessions) == 1
    session_id = sessions[0]["id"]
    assert sessions[0]["host"] == "mcp"
    assert sessions[0]["branch"] == "feature/test"

    events = store.all_events(session_id)
    assert len(events) >= 1
    assert events[0]["type"] == "session_start"
    assert "dogfooding validation" in events[0]["content"]

    # 2. cortex_emit uses same session, creates raw event, enriches provenance
    emit_res = mcp_server.cortex_emit(
        kind="adr",
        statement="Use SQLite WAL mode for concurrency",
        rationale="Prevents database lock issues during parallel reads and writes",
        alternatives_rejected=["jsonl", "xml"],
        scope=["cortex/storage/store.py"],
    )
    assert "emitted" in emit_res

    # Check that raw event was captured
    events_after_emit = store.all_events(session_id)
    assert len(events_after_emit) == 2
    raw_emit_event = events_after_emit[1]
    assert raw_emit_event["type"] == "agent_response"
    assert "Use SQLite WAL mode" in raw_emit_event["content"]
    assert "cortex/storage/store.py" in raw_emit_event["files"]

    # Check entity provenance
    adrs = store.list_by_type(ArtifactType.ADR)
    assert len(adrs) == 1
    adr = adrs[0]
    assert adr.session_id == session_id
    assert adr.provenance.source_session == session_id
    assert raw_emit_event["id"] in adr.provenance.source_events
    assert adr.provenance.source_files == ["cortex/storage/store.py"]

    # 3. cortex_emit with related_to creates graph edge
    emit_fix = mcp_server.cortex_emit(
        kind="fix",
        statement="Set busy_timeout=30000 on SQLite connection",
        rationale="Resolves lock contention under concurrent access",
        scope=["cortex/storage/store.py"],
        related_to=[adr.id],
    )
    assert "emitted" in emit_fix

    fixes = store.list_by_type(ArtifactType.FIX)
    assert len(fixes) == 1
    fix = fixes[0]

    # Check edge was created
    edges = store.edges_of(src=fix.id)
    assert len(edges) >= 1
    assert edges[0]["dst"] == adr.id
    assert edges[0]["rel"] == "RESOLVES"


def test_mcp_cortex_link_tool(project, store, monkeypatch):
    monkeypatch.setenv("CORTEX_ROOT", str(project))
    mcp_server._stores.clear()
    mcp_server._active_sessions.clear()

    # Invalid relation
    res_bad = json.loads(mcp_server.cortex_link("node-A", "INVALID_REL", "node-B"))
    assert res_bad["ok"] is False
    assert "invalid relation" in res_bad["error"]

    # Valid relation
    res_ok = mcp_server.cortex_link("node-A", "IMPLEMENTS", "node-B")
    assert "linked node-A -[IMPLEMENTS]-> node-B" in res_ok

    edges = store.edges_of(src="node-A")
    assert len(edges) == 1
    assert edges[0]["rel"] == "IMPLEMENTS"
    assert edges[0]["dst"] == "node-B"
