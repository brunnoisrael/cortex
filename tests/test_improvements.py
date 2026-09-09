"""Regression tests for the improvement waves (Ondas 1-5)."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from cortex.capture.recorder import capture_event
from cortex.compiler.compiler import CompileInput, _tokens, compile_context
from cortex.distillation.engine import DistillationEngine
from cortex.knowledge.models import ArtifactType, Authority, Entity, Freshness, Provenance, Status
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


# ---------- Onda 1.1: search respects requested limit ----------

def test_search_respects_requested_limit(store):
    # Create 30 ADRs directly to test search limit without relying on extraction
    for i in range(30):
        entity = Entity(
            id=f"adr-{i:04d}",
            type=ArtifactType.ADR,
            statement=f"Decision {i}: Use PostgreSQL for module {i}",
            status=Status.ACTIVE,
            authority=Authority.HUMAN_CONFIRMED,
            confidence=0.95,
            scope=[f"src/module{i}/"],
            details={"decision": f"Use PostgreSQL for module {i}"},
            provenance=Provenance(
                source_session="test",
                source_events=[],
                source_files=[],
                source_commits=[],
                source_entities=[],
                generated_at=datetime.now(UTC).isoformat(),
                extraction_source="test"
            ),
            freshness=Freshness(
                last_verified_at=None,
                verification_source=None,
                stale_after_days=90,
                stale=False
            ),
            superseded_by=None,
            created_at=datetime.now(UTC).isoformat(),
            updated_at=datetime.now(UTC).isoformat(),
        )
        store.upsert(entity)

    hits = store.search("PostgreSQL", limit=200)
    assert len(hits) > 20, (
        f"search() capou o pedido de 200 para {len(hits)} — recall híbrido degradado"
    )


# ---------- Onda 1.2: visualizer escapes HTML ----------

def test_visualizer_escapes_statement_html(tmp_path, store):
    # Create entity with hostile payload
    entity = Entity(
        id="adr-0001",
        type=ArtifactType.ADR,
        statement="<img src=x onerror=alert(document.cookie)>",
        status=Status.ACTIVE,
        authority=Authority.HUMAN_CONFIRMED,
        confidence=0.95,
        scope=["src/test/"],
        details={"decision": "test"},
        provenance=Provenance(
            source_session="test",
            source_events=[],
            source_files=[],
            source_commits=[],
            source_entities=[],
            generated_at=datetime.now(UTC).isoformat(),
            extraction_source="test"
        ),
        freshness=Freshness(
            last_verified_at=None,
            verification_source=None,
            stale_after_days=90,
            stale=False
        ),
        superseded_by=None,
        created_at=datetime.now(UTC).isoformat(),
        updated_at=datetime.now(UTC).isoformat(),
    )
    store.upsert(entity)

    from cortex.visualizer import generate_provenance_graph_html
    html_out = generate_provenance_graph_html(store)
    assert "<img src=x" not in html_out
    assert "&lt;img" in html_out  # escaped
    assert "</script><script>" not in html_out


# ---------- Onda 1.3: extraction failure must not mark events distilled ----------

def test_distill_does_not_mark_events_on_extraction_failure(store, monkeypatch):
    store.ensure_session("s1", "test")
    capture_event(store, {"type": "user_instruction", "session_id": "s1",
                          "content": "Vamos usar PostgreSQL porque precisamos de ACID"})
    import cortex.distillation.engine as eng
    monkeypatch.setattr(eng, "extract_decisions",
                        lambda _e: (_ for _ in ()).throw(RuntimeError("boom")))
    report = make_engine(store).distill_session("s1")
    assert report.heuristics_failed is True
    row = store.conn.execute("SELECT distilled FROM events").fetchone()
    assert row["distilled"] == 0, "evento foi marcado distilled apesar da extração falhar"
    assert report.warnings and "retry" in report.warnings[0]
    # segundo distill (sem a falha) processa o evento e aí sim marca:
    monkeypatch.undo()
    report2 = make_engine(store).distill_session("s1")
    assert report2.heuristics_failed is False
    row = store.conn.execute("SELECT distilled FROM events").fetchone()
    assert row["distilled"] == 1


# ---------- Onda 1.4: hook communicates failure via exit code ----------

def test_hook_exit_code_signals_failure(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from cortex.cli.app import app
    monkeypatch.chdir(tmp_path)  # no workspace markers → hook payload fails
    runner = CliRunner()
    payload = json.dumps({"hook_event_name": "UserPromptSubmit", "prompt": "x"})
    result = runner.invoke(app, ["hook"], input=payload)
    assert result.exit_code == 1, "host precisa descobrir a falha pelo exit code"
    out = json.loads(result.output)  # stdout JSON contract stays intact
    assert out["ok"] is False


def test_hook_exit_code_zero_on_success(project, monkeypatch):
    from typer.testing import CliRunner
    from cortex.cli.app import app
    monkeypatch.chdir(project)
    runner = CliRunner()
    payload = json.dumps({
        "session_id": "sess-cli-1", "hook_event_name": "UserPromptSubmit",
        "prompt": "Vamos usar Redis porque precisamos de cache.",
        "cwd": str(project),
    })
    result = runner.invoke(app, ["hook"], input=payload)
    assert result.exit_code == 0
    out = json.loads(result.output)
    assert out["ok"] is True


# ---------- Onda 2.1: atomic id mint across concurrent connections ----------

def test_reserve_entity_id_is_atomic_across_connections(project):
    from cortex.workspace import CORTEX_DIR
    db = project / CORTEX_DIR / "cortex.db"
    a = KnowledgeStore(db)
    b = KnowledgeStore(db)
    try:
        ids = []
        for s in (a, b) * 5:
            ids.append(s.reserve_entity_id(ArtifactType.ADR))
        assert len(set(ids)) == len(ids), f"ids duplicados: {ids}"
        assert all(isinstance(i, str) and i.startswith("adr-") for i in ids)

        # under busy_timeout, concurrent writes must not raise 'database is locked'
        import threading
        errors: list[Exception] = []

        def hammer():
            try:
                s = KnowledgeStore(db)
                try:
                    for i in range(20):
                        s.ensure_session(
                            f"s-{threading.get_ident()}-{i}", "t")
                finally:
                    s.close()
            except Exception as exc:  # pragma: no cover - failure evidence
                errors.append(exc)

        t1 = threading.Thread(target=hammer)
        t2 = threading.Thread(target=hammer)
        t1.start(); t2.start(); t1.join(); t2.join()
        assert not errors, errors
    finally:
        a.close()
        b.close()


# ---------- Onda 2.2: one malformed row must not poison readers ----------

def test_one_malformed_row_does_not_poison_reads(store):
    store.ensure_session("s1", "test")
    capture_event(store, {"type": "user_instruction", "session_id": "s1",
                          "content": "Vamos usar PostgreSQL porque ACID"})
    make_engine(store).distill_session("s1")
    assert store.all_entities()  # store has valid content
    # simulates a legacy/corrupted write
    store.conn.execute(
        "INSERT INTO entities (id, type, status, authority, confidence, statement,"
        " details, scope, provenance, freshness, created_at, updated_at)"
        " VALUES ('adr-9999', 'tipo_inexistente', 'active', 'observed', 0.5,"
        " 'x', '{}', '[]', '{}', '{}', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')")
    ents = store.all_entities()          # must NOT raise
    assert all(e.id != "adr-9999" for e in ents)
    assert store.malformed_rows == 1
    assert store.search("PostgreSQL")    # search must not raise either
    assert store.get("adr-9999") is None


# ---------- Onda 2.3: schema versioning / legacy store upgrade ----------

def test_store_upgrades_legacy_db_without_user_version(tmp_path):
    import sqlite3
    from cortex.storage.store import MIGRATIONS, SCHEMA, SCHEMA_VERSION
    db = tmp_path / "c.db"
    legacy_v1 = SCHEMA.replace("    meta TEXT,\n    host TEXT,\n", "    meta TEXT,\n")
    assert "host TEXT" not in legacy_v1.split("CREATE TABLE IF NOT EXISTS events")[1][:400], (
        "fixture não reproduziu o schema v1 (sem coluna host)"
    )
    legacy = sqlite3.connect(str(db))
    legacy.executescript(legacy_v1)
    legacy.commit()
    legacy.close()
    assert MIGRATIONS, "runner sem migrações não testa nada"
    store = KnowledgeStore(db)
    try:
        version = store.conn.execute("PRAGMA user_version").fetchone()[0]
        assert version == SCHEMA_VERSION
        cols = {r[1] for r in store.conn.execute("PRAGMA table_info(events)")}
        assert "host" in cols, "migração 002 não aplicou ALTER TABLE"
        assert store.all_entities() == []
    finally:
        store.close()


def test_fresh_store_is_current_schema(project):
    from cortex.workspace import CORTEX_DIR
    from cortex.storage.store import SCHEMA_VERSION
    store2 = KnowledgeStore(project / CORTEX_DIR / "cortex.db")
    try:
        assert store2.schema_version == SCHEMA_VERSION
        assert store2.conn.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
    finally:
        store2.close()


# ---------- Onda 2.4: capture never raises (PRD §42) ----------

def test_capture_event_never_raises(store):
    store.ensure_session("s1", "test")
    assert capture_event(store, {}) is None            # invalid shape
    assert capture_event(store, {"type": "t"}) is not None
    eid = capture_event(store, {"type": "t", "session_id": "s1"})
    dup = capture_event(store, {"type": "t", "session_id": "s1", "id": eid})
    assert dup is None, "duplicata deve ser ignorada, não exceção"


# ---------- Onda 2.5: LLM degradation with signal + honest provenance ----------

def test_llm_candidates_provenance_is_honest(store):
    from cortex.distillation.llm import llm_candidates
    events = [
        {"id": "e1", "type": "user_instruction", "session_id": "s1",
         "content": "x", "files": []},
        {"id": "e2", "type": "agent_response", "session_id": "s1",
         "content": "y", "files": []},
    ]
    raw = [
        {"type": "adr", "statement": "Use Postgres", "scope": ["src/db"]},
        {"type": "adr", "statement": "Use Redis", "scope": ["src/cache"],
         "event_ids": ["e2", "e-inventado"]},
    ]
    cands = llm_candidates(raw, events)
    assert cands[0].event_ids == [], (
        "candidato LLM sem evidência vinculável deve carregar lista vazia"
    )
    assert cands[1].event_ids == ["e2"], "ids inválidos/inventados não podem passar"


def test_llm_explicit_mode_probes_availability(store, monkeypatch):
    """llm="ollama" com servidor caído: probe de 2s, sem chamada de extract."""
    import cortex.distillation.engine as eng
    calls = {"extract": 0}
    monkeypatch.setattr(
        "cortex.distillation.llm.OllamaDistiller.available", lambda self: False)

    def _fail_extract(self, events):
        calls["extract"] += 1
        raise AssertionError("extract não deve rodar com servidor caído")

    monkeypatch.setattr("cortex.distillation.llm.OllamaDistiller.extract",
                        _fail_extract)
    store.ensure_session("s1", "test")
    capture_event(store, {"type": "user_instruction", "session_id": "s1",
                          "content": "Vamos usar Redis porque precisamos de cache."})
    report = make_engine(store, llm="ollama").distill_session("s1")
    assert not report.llm_used
    assert calls["extract"] == 0
    assert report.adrs == 1  # heurística seguiu normal


def test_engine_passes_llm_settings(store, monkeypatch):
    captured = {}
    monkeypatch.setattr(
        "cortex.distillation.llm.OllamaDistiller.available", lambda self: False)
    from cortex.distillation.llm import OllamaDistiller
    real_init = OllamaDistiller.__init__

    def spy_init(self, url="http://localhost:11434", model="qwen2.5:7b",
                 timeout=30.0):
        captured.update(url=url, model=model, timeout=timeout)
        real_init(self, url=url, model=model, timeout=timeout)

    monkeypatch.setattr(OllamaDistiller, "__init__", spy_init)
    store.ensure_session("s1", "test")
    capture_event(store, {"type": "user_instruction", "session_id": "s1",
                          "content": "Vamos usar Redis porque cache."})
    make_engine(store, llm="auto", ollama_url="http://localhost:9999",
                llm_model="llama3:8b", llm_timeout_s=7.5).distill_session("s1")
    assert captured == {"url": "http://localhost:9999",
                        "model": "llama3:8b", "timeout": 7.5}


def test_config_has_llm_model_and_timeout(tmp_path):
    from cortex.config import CortexConfig
    (tmp_path / "cortex.toml").write_text(
        '[distillation]\nllm_model = "llama3:8b"\nllm_timeout_s = 12.5\n',
        encoding="utf-8")
    cfg = CortexConfig.load(tmp_path)
    assert cfg.llm_model == "llama3:8b"
    assert cfg.llm_timeout_s == 12.5


def test_extractor_failure_is_isolated(store, monkeypatch):
    """One broken extractor must not sink the others' candidates."""
    store.ensure_session("s1", "test")
    capture_event(store, {"type": "user_instruction", "session_id": "s1",
                          "content": "Decidimos usar PostgreSQL em vez de MongoDB porque ACID"})
    import cortex.distillation.engine as eng
    monkeypatch.setattr(eng, "extract_negative_knowledge",
                        lambda _e: (_ for _ in ()).throw(RuntimeError("boom")))
    report = make_engine(store).distill_session("s1")
    assert report.heuristics_failed is True
    adrs = store.list_by_type(ArtifactType.ADR)
    assert any("PostgreSQL" in e.statement for e in adrs), (
        "falha isolada de um extrator apagou candidatos dos outros"
    )


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
