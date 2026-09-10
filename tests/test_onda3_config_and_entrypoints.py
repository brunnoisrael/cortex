"""Regression tests for Onda 3 — config and entry-surface hardening
(PLANO_ENDURECIMENTO_2026-09-08.md items 3.1-3.5)."""

from __future__ import annotations

import json

import pytest
import typer

from cortex.config import CortexConfig, CortexConfigError

# ---------- 3.1: CortexConfig.load() validates instead of raising raw ----------

def test_config_rejects_string_bool(tmp_path):
    (tmp_path / "cortex.toml").write_text('[capture]\nenabled = "false"\n', encoding="utf-8")
    with pytest.raises(CortexConfigError, match="esperado booleano"):
        CortexConfig.load(tmp_path)


def test_config_string_bool_is_not_coerced_to_true(tmp_path):
    """bool('false') == True in plain Python — the exact trap item 3.1 flags.
    Loading must raise, never silently produce capture_enabled=True."""
    (tmp_path / "cortex.toml").write_text('[capture]\nenabled = "false"\n', encoding="utf-8")
    with pytest.raises(CortexConfigError):
        CortexConfig.load(tmp_path)


def test_config_rejects_out_of_range_max_tokens(tmp_path):
    (tmp_path / "cortex.toml").write_text('[context]\nmax_tokens = -5\n', encoding="utf-8")
    with pytest.raises(CortexConfigError, match="mínimo é 100"):
        CortexConfig.load(tmp_path)


def test_config_rejects_bad_toml(tmp_path):
    (tmp_path / "cortex.toml").write_text("[capture\nbroken", encoding="utf-8")
    with pytest.raises(CortexConfigError, match="não pôde ser interpretado"):
        CortexConfig.load(tmp_path)


def test_config_rejects_non_numeric_string_for_int_field(tmp_path):
    (tmp_path / "cortex.toml").write_text(
        '[context]\nmax_tokens = "2000"\n', encoding="utf-8")
    with pytest.raises(CortexConfigError, match="esperado inteiro"):
        CortexConfig.load(tmp_path)


def test_config_truncating_float_for_int_field_rejected(tmp_path):
    (tmp_path / "cortex.toml").write_text(
        '[capture]\nraw_retention_days = 30.7\n', encoding="utf-8")
    with pytest.raises(CortexConfigError, match="esperado inteiro"):
        CortexConfig.load(tmp_path)


def test_config_rejects_unknown_llm_mode(tmp_path):
    (tmp_path / "cortex.toml").write_text('[distillation]\nllm = "gpt5"\n', encoding="utf-8")
    with pytest.raises(CortexConfigError, match="distillation.llm"):
        CortexConfig.load(tmp_path)


def test_config_rejects_unknown_distill_mode(tmp_path):
    (tmp_path / "cortex.toml").write_text('[distillation]\nmode = "realtime"\n', encoding="utf-8")
    with pytest.raises(CortexConfigError, match="distillation.mode"):
        CortexConfig.load(tmp_path)


def test_config_rejects_confidence_out_of_bounds(tmp_path):
    (tmp_path / "cortex.toml").write_text(
        '[distillation]\nmin_confidence_for_persistence = 5\n', encoding="utf-8")
    with pytest.raises(CortexConfigError, match=r"\[0,1\]"):
        CortexConfig.load(tmp_path)


def test_config_valid_file_loads_cleanly(tmp_path):
    from cortex.config import write_default_config
    write_default_config(tmp_path, "demo")
    cfg = CortexConfig.load(tmp_path)
    assert cfg.project_name == "demo"
    assert cfg.llm == "heuristic"


def test_config_missing_file_returns_defaults(tmp_path):
    cfg = CortexConfig.load(tmp_path)
    assert cfg == CortexConfig()


# ---------- 3.1 follow-up: CLI surfaces CortexConfigError cleanly ----------

def test_cli_status_reports_config_error_not_traceback(project, store, monkeypatch):
    from typer.testing import CliRunner

    from cortex.cli.app import app
    (project / "cortex.toml").write_text('[capture]\nenabled = "false"\n', encoding="utf-8")
    monkeypatch.chdir(project)
    runner = CliRunner()
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 1
    assert "esperado booleano" in result.output
    assert "Traceback" not in result.output


# ---------- 3.2: `cortex config --set` cannot inject TOML or corrupt the file ----------

def test_config_set_rejects_injection(project, monkeypatch):
    from cortex.cli.app import _config_set
    monkeypatch.chdir(project)
    before = (project / "cortex.toml").read_text(encoding="utf-8")
    with pytest.raises(typer.Exit):
        _config_set(project, "project.name", 'x\n[distillation]\nllm = "ollama"')
    assert (project / "cortex.toml").read_text(encoding="utf-8") == before, (
        "arquivo não deveria ser tocado quando o valor é rejeitado"
    )
    assert not (project / "cortex.toml.tmp").exists()


def test_config_set_no_corruption_on_invalid_value(project, monkeypatch):
    monkeypatch.chdir(project)
    from cortex.cli.app import _config_set
    before = (project / "cortex.toml").read_text(encoding="utf-8")
    with pytest.raises(typer.Exit):
        _config_set(project, "context.max_tokens", "abc")
    assert (project / "cortex.toml").read_text(encoding="utf-8") == before
    assert not (project / "cortex.toml.tmp").exists()


def test_config_set_valid_value_round_trips(project, monkeypatch):
    monkeypatch.chdir(project)
    from cortex.cli.app import _config_set
    _config_set(project, "context.max_tokens", "1500")
    cfg = CortexConfig.load(project)
    assert cfg.context_max_tokens == 1500


def test_config_set_string_value_is_quoted_safely(project, monkeypatch):
    """A string value must round-trip through TOML even with special chars,
    and can never be used to inject a new section."""
    monkeypatch.chdir(project)
    from cortex.cli.app import _config_set
    _config_set(project, "project.name", 'weird "quoted" name')
    cfg = CortexConfig.load(project)
    assert cfg.project_name == 'weird "quoted" name'


# ---------- 3.3: installer merge helpers never destroy the user's file ----------

def test_merge_json_preserves_user_config_on_invalid_json(tmp_path):
    from cortex.adapters.installer import _merge_json
    p = tmp_path / "settings.json"
    p.write_text('{"mcpServers": {"meu-servidor": {"command": "x"}}', encoding="utf-8")
    _merge_json(p, {"hooks": {"SessionStart": [{"hooks": [{"type": "command"}]}]}})
    backup = tmp_path / "settings.json.cortex-bak"
    assert backup.exists()
    assert "meu-servidor" in backup.read_text(encoding="utf-8")


def test_merge_json_appends_user_hooks_instead_of_replacing(tmp_path):
    from cortex.adapters.installer import CLAUDE_SETTINGS_SNIPPET, _merge_json
    p = tmp_path / "settings.json"
    user_hook = {"matcher": "", "hooks": [{"type": "command", "command": "meu-script.sh"}]}
    p.write_text(json.dumps({"hooks": {"SessionStart": [user_hook]}}), encoding="utf-8")
    _merge_json(p, CLAUDE_SETTINGS_SNIPPET)
    merged = json.loads(p.read_text(encoding="utf-8"))["hooks"]["SessionStart"]
    assert len(merged) == 2, "hook do usuário foi substituído em vez de anexado"
    assert user_hook in merged


def test_merge_json_no_orphan_tmp_file(tmp_path):
    from cortex.adapters.installer import _merge_json
    p = tmp_path / "settings.json"
    _merge_json(p, {"hooks": {"Stop": [{"hooks": [{"type": "command"}]}]}})
    assert not (tmp_path / "settings.json.tmp").exists()


def test_cursor_session_id_write_is_atomic(tmp_path):
    from cortex.adapters.installer import _cursor_session_id
    sid1 = _cursor_session_id(tmp_path)
    sid2 = _cursor_session_id(tmp_path)  # within idle window: same session
    assert sid1 == sid2
    assert not (tmp_path / "cursor_session.json.tmp").exists()


def test_cursor_session_id_survives_corrupted_state(tmp_path):
    from cortex.adapters.installer import _cursor_session_id
    state_path = tmp_path / "cursor_session.json"
    tmp_path.mkdir(parents=True, exist_ok=True)
    state_path.write_text("{not json", encoding="utf-8")
    sid = _cursor_session_id(tmp_path)  # must not raise
    assert sid.startswith("sess-cursor-")


# ---------- 3.4: privacy.network_calls gates non-loopback Ollama ----------

def test_llm_skipped_for_remote_url_without_network_calls(store, monkeypatch):
    from cortex.capture.recorder import capture_event
    from cortex.distillation.engine import DistillationEngine

    calls = {"available": 0}
    monkeypatch.setattr(
        "cortex.distillation.llm.OllamaDistiller.available",
        lambda self: calls.__setitem__("available", calls["available"] + 1) or False,
    )
    store.ensure_session("s1", "test")
    capture_event(store, {"type": "user_instruction", "session_id": "s1",
                          "content": "Vamos usar Redis porque cache."})
    engine = DistillationEngine(
        store, llm="auto", ollama_url="http://10.0.0.5:11434", network_calls=False,
    )
    engine.distill_session("s1")
    assert calls["available"] == 0, "remote ollama_url must not be probed without network_calls=true"


def test_llm_allowed_for_loopback_url_without_network_calls(store, monkeypatch):
    from cortex.capture.recorder import capture_event
    from cortex.distillation.engine import DistillationEngine

    calls = {"available": 0}

    def _spy(self):
        calls["available"] += 1
        return False

    monkeypatch.setattr("cortex.distillation.llm.OllamaDistiller.available", _spy)
    store.ensure_session("s1", "test")
    capture_event(store, {"type": "user_instruction", "session_id": "s1",
                          "content": "Vamos usar Redis porque cache."})
    engine = DistillationEngine(
        store, llm="auto", ollama_url="http://localhost:11434", network_calls=False,
    )
    engine.distill_session("s1")
    assert calls["available"] == 1, "loopback ollama_url is local, not a network call"


# ---------- 3.5: `hook --install` writes to the detected workspace, not cwd ----------

def test_hook_install_writes_to_workspace_root_not_subdirectory(project, monkeypatch):
    from typer.testing import CliRunner

    from cortex.cli.app import app
    subdir = project / "src" / "handlers"
    monkeypatch.chdir(subdir)
    runner = CliRunner()
    result = runner.invoke(app, ["hook", "--install", "claude-code"])
    assert result.exit_code == 0
    assert (project / ".claude" / "settings.json").exists()
    assert not (subdir / ".claude").exists()


def test_hook_install_requires_a_workspace(tmp_path, monkeypatch):
    from typer.testing import CliRunner

    from cortex.cli.app import app
    monkeypatch.chdir(tmp_path)  # no git root, no cortex.toml, no manifest
    runner = CliRunner()
    result = runner.invoke(app, ["hook", "--install", "claude-code"])
    assert result.exit_code == 1
    assert "no workspace" in result.output.lower()
