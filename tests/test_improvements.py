"""Regression tests for the improvement waves (Ondas 1-5)."""

from __future__ import annotations

import json

from cortex.capture.recorder import capture_event
from cortex.compiler.compiler import CompileInput, _tokens, compile_context
from cortex.distillation.engine import DistillationEngine
from cortex.knowledge.models import ArtifactType, Authority
from cortex.storage.store import KnowledgeStore


def make_engine(store, **kw) -> DistillationEngine:
    return DistillationEngine(store, **kw)


# ---------- Onda 1: auto-distill on session end (P0.2) ----------

def test_stop_hook_auto_distills(project):
    from cortex.adapters.installer import handle_hook_payload
    handle_hook_payload({
        "session_id": "sess-auto-1", "hook_event_name": "UserPromptSubmit",
        "prompt": "Vamos usar Kafka porque precisamos de fila durável.",
        "cwd": str(project),
    }, project)
    result = handle_hook_payload({
        "session_id": "sess-auto-1", "hook_event_name": "Stop",
        "cwd": str(project),
    }, project)
    assert result["ok"] is True
    assert "distilled" in result, "Stop hook must trigger offline distillation"
    s = KnowledgeStore(project / ".cortex" / "cortex.db")
    adrs = s.list_by_type(ArtifactType.ADR)
    assert any("Kafka" in e.statement for e in adrs)
    reviews = s.list_by_type(ArtifactType.REVIEW)
    assert any(r.session_id == "sess-auto-1" for r in reviews)
    # session closed by the review
    assert s.get_session("sess-auto-1")["ended_at"] is not None
    s.close()


# ---------- Onda 1: MCP requires explicit workspace (P0.3) ----------

def test_mcp_rejects_uninitialized_cwd(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("CORTEX_ROOT", raising=False)
    import pytest

    from cortex.server.mcp_server import _ws
    with pytest.raises(RuntimeError):
        _ws()


def test_mcp_accepts_initialized_workspace(project, monkeypatch):
    monkeypatch.chdir(project)
    monkeypatch.delenv("CORTEX_ROOT", raising=False)
    from cortex.server.mcp_server import _ws
    ws, cfg = _ws()
    assert ws.root == project


# ---------- Onda 2: semantic dedup strengthens instead of duplicating ----------

def test_semantic_dedup_merges_paraphrases(store):
    sess = store.ensure_session
    sess("s1", "test")
    capture_event(store, {"type": "user_instruction", "session_id": "s1",
                          "content": "Vamos usar PostgreSQL para transações ACID.",
                          "files": ["src/db/"]})
    make_engine(store).distill_session("s1")
    sess("s2", "test")
    capture_event(store, {"type": "user_instruction", "session_id": "s2",
                          "content": "Decidimos: usar PostgreSQL para as transações ACID do sistema.",
                          "files": ["src/db/"]})
    report = make_engine(store).distill_session("s2")
    assert report.deduplicated == 1
    adrs = store.list_by_type(ArtifactType.ADR)
    assert len(adrs) == 1
    assert len(adrs[0].provenance.source_events) == 2, "merged entity keeps both evidences"
    assert adrs[0].confidence > 0.95 - 0.01


# ---------- Onda 3: commits as evidence ----------

def test_commits_become_evidence(project):
    import subprocess
    (project / "src" / "db").mkdir(exist_ok=True)
    (project / "src" / "db" / "schema.sql").write_text("CREATE TABLE t();\n")
    subprocess.run(["git", "-C", str(project), "add", "."], check=True)
    subprocess.run(["git", "-C", str(project), "commit", "-qm",
                    "chore: decidimos migrar para Postgres porque precisamos de ACID"], check=True)
    store = KnowledgeStore(project / ".cortex" / "cortex.db")
    from cortex.capture.recorder import capture_commits
    ids = capture_commits(store, project)
    assert ids
    report = make_engine(store).distill_all()
    assert report.adrs == 1
    adr = store.list_by_type(ArtifactType.ADR)[0]
    assert adr.authority == Authority.OBSERVED  # git evidence, below explicit statement
    assert adr.provenance.source_commits, "ADR points to the commit hash"
    store.close()


# ---------- Onda 3: LLM candidate conversion + auto fallback ----------

def test_llm_candidates_conversion():
    from cortex.distillation.llm import llm_candidates
    events = [{"id": "e1", "type": "user_instruction", "session_id": "s1",
               "content": "x", "files": []}]
    raw = [{"type": "adr", "statement": "Use Postgres for transactions",
            "details": {"decision": "Postgres"}, "scope": ["src/db"]},
           {"type": "bogus", "statement": "ignored"}]
    cands = llm_candidates(raw, events)
    assert len(cands) == 1
    assert cands[0].source == "llm_inference"  # bottom of inference hierarchy
    assert cands[0].confidence == 0.65


def test_llm_auto_mode_falls_back_silently(store, monkeypatch):
    from cortex.distillation import llm as llm_mod
    monkeypatch.setattr(llm_mod.OllamaDistiller, "available", lambda self: False)
    sess = store.ensure_session
    sess("s1", "test")
    capture_event(store, {"type": "user_instruction", "session_id": "s1",
                          "content": "Vamos usar Redis porque precisamos de cache.",
                          "files": ["src/cache/"]})
    report = make_engine(store, llm="auto").distill_session("s1")
    assert not report.llm_used
    assert report.adrs == 1  # heuristic extraction still ran


# ---------- Onda 4: honest verification (P1.3) ----------

def test_verify_honest_promotes_only_with_evidence(project):
    (project / "src" / "db").mkdir(exist_ok=True)
    (project / "src" / "db" / "schema.sql").write_text(
        "CREATE TABLE webhook_payload (id int);\n-- PostgreSQL specific\n")
    store = KnowledgeStore(project / ".cortex" / "cortex.db")
    store.ensure_session("s1", "test")
    capture_event(store, {"type": "user_instruction", "session_id": "s1",
                          "content": "Decidimos usar PostgreSQL para transações.",
                          "files": ["src/db"]})
    make_engine(store).distill_session("s1")
    adr = store.list_by_type(ArtifactType.ADR)[0]

    from cortex.verification import verify_entity
    # symbol "PostgreSQL" exists in src/db -> honest promotion
    result = verify_entity(store, project, adr)
    assert result["status"] == "verified"
    assert store.get(adr.id).authority == Authority.REPOSITORY_VERIFIED

    # scope disappears -> stale
    adr2 = store.list_by_type(ArtifactType.ADR)[0]
    adr2.scope = ["src/deleted-path"]
    store.upsert(adr2)
    result = verify_entity(store, project, store.get(adr2.id))
    assert result["status"] == "stale"
    assert store.get(adr2.id).freshness.stale
    store.close()


def test_verify_refuses_promotion_without_evidence(project, store):
    (project / "src" / "db").mkdir(exist_ok=True)
    (project / "src" / "db" / "notes.txt").write_text("nothing relevant here\n")
    store.ensure_session("s1", "test")
    capture_event(store, {"type": "user_instruction", "session_id": "s1",
                          "content": "Decidimos usar MongoDB Atlas para documentos.",
                          "files": ["src/db"]})
    make_engine(store).distill_session("s1")
    adr = store.list_by_type(ArtifactType.ADR)[0]
    from cortex.verification import verify_entity
    result = verify_entity(store, project, adr)
    assert result["status"] == "unverified"
    assert store.get(adr.id).authority != Authority.REPOSITORY_VERIFIED


# ---------- Onda 4: stable Cursor session ids (P1.6) ----------

def test_cursor_session_ids_stable_then_rotate(project, tmp_path):
    from cortex.adapters.installer import _cursor_session_id
    from cortex.workspace import detect_workspace
    ws = detect_workspace(project)
    sid1 = _cursor_session_id(ws.cortex_dir)
    sid2 = _cursor_session_id(ws.cortex_dir)
    assert sid1 == sid2, "prompts in the same session share the id"
    # simulate idle gap
    import time
    state = ws.cortex_dir / "cursor_session.json"
    data = json.loads(state.read_text())
    data["last_seen"] = time.time() - 3600
    state.write_text(json.dumps(data))
    sid3 = _cursor_session_id(ws.cortex_dir)
    assert sid3 != sid1, "idle gap rotates the session id"


# ---------- Onda 4: CLI additions ----------

def test_cli_diff_retrieval_debug_benchmark_config(project, monkeypatch):
    monkeypatch.chdir(project)
    from typer.testing import CliRunner

    from cortex.cli.app import app as cli_app
    runner = CliRunner()
    store = KnowledgeStore(project / ".cortex" / "cortex.db")
    store.ensure_session("s1", "cli")
    capture_event(store, {"type": "user_instruction", "session_id": "s1",
                          "content": "Decidimos usar SQLite porque zero configuração.",
                          "files": ["src/db"]})
    make_engine(store).distill_session("s1")
    store.close()

    r = runner.invoke(cli_app, ["diff", "--sessions", "2"])
    assert r.exit_code == 0 and "adr" in r.output

    r = runner.invoke(cli_app, ["retrieval-debug", "sqlite configuração"])
    assert r.exit_code == 0 and "bm25 hits" in r.output and "score=" in r.output

    r = runner.invoke(cli_app, ["benchmark"])
    assert r.exit_code == 0 and "8/8" in r.output

    r = runner.invoke(cli_app, ["config", "--set", "context.max_tokens", "1500"])
    assert r.exit_code == 0
    toml_text = (project / "cortex.toml").read_text(encoding="utf-8")
    assert "max_tokens = 1500" in toml_text
    r = runner.invoke(cli_app, ["config", "--set", "chave.inexistente", "1"])
    assert r.exit_code == 1, "invalid keys are rejected"

    r = runner.invoke(cli_app, ["phase"])
    assert r.exit_code == 0 and "PHASE REVIEW" in r.output

    r = runner.invoke(cli_app, ["status", "--verbose"])
    assert r.exit_code == 0 and "[debug] distill" in r.output


# ---------- Onda 4: semantic contradiction (P1.1) ----------

def test_contradiction_handles_version_variants(store):
    store.ensure_session("s1", "test")
    capture_event(store, {"type": "user_instruction", "session_id": "s1",
                          "content": "Decidimos PostgreSQL em vez de MySQL porque ACID.",
                          "files": ["src/db/"]})
    make_engine(store).distill_session("s1")
    store.ensure_session("s2", "test")
    capture_event(store, {"type": "user_instruction", "session_id": "s2",
                          "content": "Vamos usar MySQL 8 para o catálogo porque simplicidade.",
                          "files": ["src/db/"]})
    make_engine(store).distill_session("s2")
    edges = store.edges_of(rel="CONTRADICTS")
    assert edges, "MySQL 8 decision contradicts the ADR that rejected MySQL"
    # ...and a paraphrase that shares no tokens must NOT be flagged
    store.ensure_session("s3", "test")
    capture_event(store, {"type": "user_instruction", "session_id": "s3",
                          "content": "Vamos usar Redis para cache porque latência.",
                          "files": ["src/cache/"]})
    make_engine(store).distill_session("s3")
    assert len(store.edges_of(rel="CONTRADICTS")) == len(edges), "unrelated decision not flagged"


# ---------- Onda 2: word-based token estimate (P2.2) ----------

def test_token_estimate_word_based():
    text = "palavra " * 100
    assert _tokens(text) == 140  # 100 words * 1.4


# ---------- negative knowledge survives supersession (PRD §44.4) ----------

def test_supersede_inherits_rejected_alternatives(store):
    store.ensure_session("s1", "test")
    capture_event(store, {"type": "user_instruction", "session_id": "s1",
                          "content": "Decidimos PostgreSQL em vez de MongoDB porque ACID.",
                          "files": ["src/db/"]})
    make_engine(store).distill_session("s1")
    store.ensure_session("s2", "test")
    capture_event(store, {"type": "user_instruction", "session_id": "s2",
                          "content": "Decidimos Aurora Postgres em vez de PostgreSQL puro porque gerenciado.",
                          "files": ["src/db/"]})
    make_engine(store).distill_session("s2")
    adrs = sorted(store.list_by_type(ArtifactType.ADR), key=lambda e: e.id)
    store.supersede(adrs[0].id, adrs[1].id)
    new = store.get(adrs[1].id)
    assert "MongoDB" in new.details["alternatives_rejected"], \
        "old rejection survives the supersession"
    ctx = compile_context(store, CompileInput(query="escolher banco", files=["src/db/"]))
    assert "MongoDB" in ctx
