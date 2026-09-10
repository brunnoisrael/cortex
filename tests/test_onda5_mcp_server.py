"""Regression tests for PLANO_ENDURECIMENTO_2026-09-08.md item 5.6:
MCP server store caching and clean kind-validation errors."""

from __future__ import annotations

import json

import cortex.server.mcp_server as mcp_server
from cortex.storage.store import KnowledgeStore


def test_cortex_remember_invalid_kind_returns_json_error_not_exception(project, monkeypatch):
    monkeypatch.setenv("CORTEX_ROOT", str(project))
    result = mcp_server.cortex_remember(statement="x", kind="banana")
    data = json.loads(result)
    assert data["ok"] is False
    assert "banana" in data["error"]
    assert "intention" in data["error"]  # a valid kind is suggested


def test_cortex_emit_invalid_kind_returns_json_error_not_exception(project, monkeypatch):
    monkeypatch.setenv("CORTEX_ROOT", str(project))
    result = mcp_server.cortex_emit(kind="banana", statement="x")
    data = json.loads(result)
    assert data["ok"] is False
    assert "banana" in data["error"]


def test_cortex_emit_negative_knowledge_alias_still_works(project, monkeypatch):
    monkeypatch.setenv("CORTEX_ROOT", str(project))
    result = mcp_server.cortex_emit(kind="negative_knowledge", statement="Não usar X")
    assert "emitted" in result


def test_store_is_cached_across_tool_calls_same_workspace(project, monkeypatch):
    """Item 5.6's acceptance test: two tool calls against the same workspace
    must not re-run the schema DDL twice."""
    monkeypatch.setenv("CORTEX_ROOT", str(project))
    mcp_server._stores.clear()  # isolate from any state left by earlier tests

    init_calls = {"n": 0}
    real_init = KnowledgeStore.__init__

    def counting_init(self, db_path):
        init_calls["n"] += 1
        real_init(self, db_path)

    monkeypatch.setattr(KnowledgeStore, "__init__", counting_init)

    mcp_server.cortex_status()
    mcp_server.cortex_status()

    assert init_calls["n"] == 1, "KnowledgeStore (and its DDL) must only be built once per workspace"
    mcp_server._stores.clear()


def test_store_cache_is_keyed_by_workspace(tmp_path, monkeypatch):
    """Two different workspaces must not share a cached connection."""
    from cortex.config import write_default_config
    from cortex.workspace import ensure_cortex_dir

    mcp_server._stores.clear()
    ws_a = tmp_path / "a"
    ws_b = tmp_path / "b"
    for ws in (ws_a, ws_b):
        ws.mkdir()
        write_default_config(ws, ws.name)
        ensure_cortex_dir(ws)

    monkeypatch.setenv("CORTEX_ROOT", str(ws_a))
    mcp_server.cortex_remember(statement="only in A", kind="intention")

    monkeypatch.setenv("CORTEX_ROOT", str(ws_b))
    mcp_server.cortex_remember(statement="only in B", kind="intention")

    assert len(mcp_server._stores) == 2
    with KnowledgeStore(ws_a / ".cortex" / "cortex.db") as fresh_a:
        statements_a = [e.statement for e in fresh_a.all_entities()]
    with KnowledgeStore(ws_b / ".cortex" / "cortex.db") as fresh_b:
        statements_b = [e.statement for e in fresh_b.all_entities()]
    assert "only in A" in statements_a and "only in A" not in statements_b
    assert "only in B" in statements_b and "only in B" not in statements_a
    mcp_server._stores.clear()
