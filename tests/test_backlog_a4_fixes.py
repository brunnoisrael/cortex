"""Regression tests for a handful of PLANO_ENDURECIMENTO_2026-09-08.md
Apêndice A.4 (low-priority backlog) findings fixed as part of finishing the
plan: these weren't scheduled into a numbered Onda, but were quick, safe,
and clearly-scoped enough to close out alongside the rest."""

from __future__ import annotations

import logging

import pytest

from cortex.compiler.compiler import CompileInput, rank


def test_rank_rejects_typo_in_weights_override(store):
    """compiler.py:97-98 (A.4): a typo'd weight key ("authoriry" instead of
    "authority") used to be silently ignored via dict-merge — the caller's
    calibration change never took effect and nothing said so. Now raises,
    since this is an explicit opt-in advanced parameter nothing on the
    agent-blocking hot path ever passes (only deliberate callers use it),
    so raising loudly here doesn't violate 'never block the agent'."""
    with pytest.raises(ValueError, match="authoriry"):
        rank(store, CompileInput(query="x"), weights_override={"authoriry": 2.0})


def test_rank_accepts_valid_weight_override(store):
    items = rank(store, CompileInput(query="x"), weights_override={"authority": 2.0})
    assert items == []  # empty store, but must not raise


def test_rank_logs_instead_of_silently_swallowing_search_failure(store, monkeypatch, caplog):
    """compiler.py:127-128 (A.4): `except Exception: fts = {}` hid a broken
    store's search() failure entirely — ranking degraded (correctly, per
    Principle 1) but with zero signal that anything went wrong."""
    def boom(*a, **kw):
        raise RuntimeError("fts5 index corrupted")

    monkeypatch.setattr(store, "search", boom)
    with caplog.at_level(logging.WARNING, logger="cortex.compiler"):
        items = rank(store, CompileInput(query="anything"))
    assert items == []  # still degrades, doesn't raise
    assert any("fts5 index corrupted" in r.message or
               (r.exc_info and "fts5 index corrupted" in str(r.exc_info[1]))
               for r in caplog.records)


def test_cortex_diff_clamps_negative_limit(project, monkeypatch):
    """mcp_server.py:357-359 (A.4): SQLite treats `LIMIT -1` as unlimited —
    cortex_diff(last_n_sessions=-1) used to dump the entire session history
    instead of erroring or clamping to a bounded window."""
    import cortex.server.mcp_server as mcp_server
    mcp_server._stores.clear()
    monkeypatch.setenv("CORTEX_ROOT", str(project))
    for i in range(5):
        mcp_server.cortex_capture(event_type="user_instruction",
                                   content=f"event {i}", session_id=f"s{i}")
    import json as _json
    result = _json.loads(mcp_server.cortex_diff(last_n_sessions=-1))
    assert len(result) <= 1, "negative last_n_sessions must clamp, not mean 'unlimited'"
    mcp_server._stores.clear()


def test_run_ccb_cleans_up_tempdir_when_setup_fails(monkeypatch):
    """ccb.py:65-73 (A.4): a failure between creating the TemporaryDirectory
    and entering the try block used to leak it on disk — moved the whole
    setup inside try/finally."""
    from cortex.benchmarks import ccb
    created: list = []
    real_tempdir = ccb.tempfile.TemporaryDirectory

    def spy_tempdir(*a, **kw):
        t = real_tempdir(*a, **kw)
        created.append(t)
        return t

    monkeypatch.setattr(ccb.tempfile, "TemporaryDirectory", spy_tempdir)
    monkeypatch.setattr(ccb, "write_default_config",
                        lambda *a, **kw: (_ for _ in ()).throw(RuntimeError("disk full")))

    with pytest.raises(RuntimeError, match="disk full"):
        ccb.run_ccb()

    assert created, "TemporaryDirectory was never constructed"
    import os
    assert not os.path.exists(created[0].name), "tempdir must be cleaned up even on setup failure"


def test_version_is_single_sourced_from_pyproject():
    """pyproject.toml + __init__.py (A.4): __version__ used to be a second
    hardcoded literal that could silently drift from pyproject.toml's
    [project] version. Now read back through installed package metadata."""
    import re
    import tomllib
    from pathlib import Path

    import cortex

    pyproject = Path(cortex.__file__).resolve().parent.parent / "pyproject.toml"
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    assert re.match(r"^\d+\.\d+\.\d+", cortex.__version__)
    assert cortex.__version__ == data["project"]["version"]


def test_distill_warns_on_unknown_session_typo(project, store, monkeypatch):
    """app.py:251 (A.4): `cortex distill --session <typo>` used to report
    'distillation complete' with 0 events processed, indistinguishable from
    a legitimate session with nothing left to distill."""
    from typer.testing import CliRunner

    from cortex.cli.app import app
    monkeypatch.chdir(project)
    runner = CliRunner()

    result = runner.invoke(app, ["distill", "--session", "sess-typo-xyz"])

    assert result.exit_code == 0  # still a diagnostic warning, not a hard failure
    assert "not found" in result.output
    assert "sess-typo-xyz" in result.output


def test_distill_no_warning_for_real_session(project, store, monkeypatch):
    from typer.testing import CliRunner

    from cortex.cli.app import app
    store.ensure_session("sess-real-1", "test")
    monkeypatch.chdir(project)
    runner = CliRunner()

    result = runner.invoke(app, ["distill", "--session", "sess-real-1"])

    assert result.exit_code == 0
    assert "not found" not in result.output
