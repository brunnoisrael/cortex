"""CliRunner tests for the governance command surface (item 4.3):
correnda confirm/reject, adr accept/reject, supersede, verify, why.

These exercise the actual Typer commands end-to-end (argument parsing,
_require_workspace, exit codes, and the store mutation), not just the
underlying KnowledgeStore methods that other test files already cover.

Every governance command closes its own store connection on the way out
(the real _require_workspace() opens a fresh one per invocation) — so after
invoking a command, tests re-open a fresh KnowledgeStore on the same db
file to assert on persisted state, rather than reusing the now-closed
`store` fixture connection."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from cortex.cli.app import app
from cortex.config import CortexConfig
from cortex.knowledge.models import ArtifactType, Authority, Entity, Status
from cortex.storage.store import KnowledgeStore
from cortex.workspace import CORTEX_DIR

runner = CliRunner()


def _seed(store, **kwargs) -> Entity:
    defaults = dict(
        id=kwargs.pop("id", "ent-1"),
        type=ArtifactType.CORRENDA,
        statement="Sempre validar entrada do usuário antes de persistir.",
        status=Status.PROPOSED,
        authority=Authority.AGENT_INFERRED,
    )
    defaults.update(kwargs)
    ent = Entity(**defaults)
    store.upsert(ent)
    return ent


def _patch_workspace(monkeypatch, project, store, cfg: CortexConfig | None = None):
    monkeypatch.setattr("cortex.cli.app._require_workspace",
                        lambda: (project, cfg or CortexConfig(), store))


def _reopen(project) -> KnowledgeStore:
    """Read back persisted state through a fresh connection, since the
    command under test already closed the one it was given."""
    return KnowledgeStore(project / CORTEX_DIR / "cortex.db")


# ---------- correnda confirm/reject ----------

def test_correnda_confirm_via_cli(project, store, monkeypatch):
    _seed(store, id="cor-1", type=ArtifactType.CORRENDA)
    _patch_workspace(monkeypatch, project, store)

    result = runner.invoke(app, ["correnda", "confirm", "cor-1"])
    assert result.exit_code == 0, result.output

    with _reopen(project) as fresh:
        ent = fresh.get("cor-1")
        assert ent.status == Status.ACTIVE
        assert ent.authority == Authority.HUMAN_CONFIRMED
        assert ent.details["confirmed_by_human"] is True


def test_correnda_confirm_unknown_id_exits_nonzero(project, store, monkeypatch):
    _patch_workspace(monkeypatch, project, store)

    result = runner.invoke(app, ["correnda", "confirm", "does-not-exist"])

    assert result.exit_code == 1


def test_correnda_reject_via_cli(project, store, monkeypatch):
    _seed(store, id="cor-2", type=ArtifactType.CORRENDA)
    _patch_workspace(monkeypatch, project, store)

    result = runner.invoke(app, ["correnda", "reject", "cor-2"])
    assert result.exit_code == 0, result.output

    with _reopen(project) as fresh:
        assert fresh.get("cor-2").status == Status.REJECTED


# ---------- adr accept/reject (registered as the "adrs" sub-app) ----------

def test_adr_accept_via_cli(project, store, monkeypatch):
    _seed(store, id="adr-1", type=ArtifactType.ADR)
    _patch_workspace(monkeypatch, project, store)

    result = runner.invoke(app, ["adrs", "accept", "adr-1"])
    assert result.exit_code == 0, result.output

    with _reopen(project) as fresh:
        ent = fresh.get("adr-1")
        assert ent.status == Status.ACTIVE
        assert ent.authority == Authority.HUMAN_CONFIRMED


def test_adr_reject_via_cli(project, store, monkeypatch):
    _seed(store, id="adr-2", type=ArtifactType.ADR)
    _patch_workspace(monkeypatch, project, store)

    result = runner.invoke(app, ["adrs", "reject", "adr-2"])
    assert result.exit_code == 0, result.output

    with _reopen(project) as fresh:
        assert fresh.get("adr-2").status == Status.REJECTED


# ---------- supersede ----------

def test_supersede_preserves_history_via_cli(project, store, monkeypatch):
    _seed(store, id="adr-old", statement="Usar MySQL.", type=ArtifactType.ADR,
          status=Status.ACTIVE)
    _seed(store, id="adr-new", statement="Usar PostgreSQL.", type=ArtifactType.ADR,
          status=Status.PROPOSED)
    _patch_workspace(monkeypatch, project, store)

    result = runner.invoke(app, ["supersede", "adr-old", "--with", "adr-new"])
    assert result.exit_code == 0, result.output

    with _reopen(project) as fresh:
        old = fresh.get("adr-old")
        assert old is not None, "superseded entity must still be retrievable (history preserved)"
        assert old.status == Status.SUPERSEDED
        assert old.superseded_by == "adr-new"
        all_ids = [e.id for e in fresh.all_entities()]
        assert "adr-old" in all_ids, "supersede must not remove the old entity from history"


def test_supersede_unknown_id_exits_nonzero(project, store, monkeypatch):
    _seed(store, id="adr-real", type=ArtifactType.ADR)
    _patch_workspace(monkeypatch, project, store)

    result = runner.invoke(app, ["supersede", "does-not-exist", "--with", "adr-real"])

    assert result.exit_code == 1


# ---------- verify ----------

def test_verify_unknown_id_exits_nonzero(project, store, monkeypatch):
    _patch_workspace(monkeypatch, project, store)

    result = runner.invoke(app, ["verify", "does-not-exist"])

    assert result.exit_code == 1


def test_verify_reports_on_known_entity(project, store, monkeypatch):
    _seed(store, id="fix-1", type=ArtifactType.FIX,
          statement="Corrigido bug no webhook_handler.py")
    _patch_workspace(monkeypatch, project, store)

    result = runner.invoke(app, ["verify", "fix-1"])

    assert result.exit_code == 0
    assert "fix-1" in result.output


# ---------- why ----------

def test_why_unknown_id_exits_nonzero(project, store, monkeypatch):
    _patch_workspace(monkeypatch, project, store)

    result = runner.invoke(app, ["why", "does-not-exist"])

    assert result.exit_code == 1


def test_why_shows_provenance_for_known_entity(project, store, monkeypatch):
    ent = _seed(store, id="adr-3", type=ArtifactType.ADR, statement="Usar Redis para cache.")
    ent.provenance.source_session = "s1"
    store.upsert(ent)
    _patch_workspace(monkeypatch, project, store)

    result = runner.invoke(app, ["why", "adr-3"])

    assert result.exit_code == 0
    assert "Usar Redis para cache." in result.output
    assert "s1" in result.output


# ---------- 5.1: workspace_store() closes the connection even on exceptions ----------

def test_workspace_store_closes_connection_on_command_exception(project, store, monkeypatch):
    """verify() calling a monkeypatched verify_entity that raises must still
    leave the store connection closed, not leaked (item 5.1's acceptance
    criterion)."""
    _seed(store, id="fix-err", type=ArtifactType.FIX, statement="algo")
    _patch_workspace(monkeypatch, project, store)
    monkeypatch.setattr(
        "cortex.verification.verify_entity",
        lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("boom")),
    )

    result = runner.invoke(app, ["verify", "fix-err"])

    assert result.exit_code != 0
    import sqlite3
    with pytest.raises(sqlite3.ProgrammingError):
        store.conn.execute("SELECT 1")


def test_workspace_store_closes_connection_on_not_found(project, store, monkeypatch):
    """The plain 'not found' -> typer.Exit(1) path must also close, not just
    the success path."""
    _patch_workspace(monkeypatch, project, store)

    result = runner.invoke(app, ["correnda", "confirm", "does-not-exist"])

    assert result.exit_code == 1
    import sqlite3
    with pytest.raises(sqlite3.ProgrammingError):
        store.conn.execute("SELECT 1")
