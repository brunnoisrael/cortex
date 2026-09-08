"""Acceptance criteria A-H from PRD §58 plus component tests."""

from __future__ import annotations

from cortex.capture.recorder import capture_event
from cortex.compiler.compiler import CompileInput, compile_context, rank
from cortex.config import CortexConfig
from cortex.distillation.engine import DistillationEngine
from cortex.distillation.review import build_session_review
from cortex.knowledge.models import ArtifactType, Status
from cortex.storage.store import KnowledgeStore


def make_engine(store: KnowledgeStore) -> DistillationEngine:
    cfg = CortexConfig()
    return DistillationEngine(store, min_confidence=cfg.min_confidence_for_persistence,
                              correnda_min_evidence=cfg.correnda_min_evidence)


def sess(store: KnowledgeStore, sid: str) -> None:
    store.ensure_session(sid, host="test")


# ---------- criterion A: decision from session 1 recovered in session 3 ----------

def test_A_decision_survives_to_later_session(store):
    sess(store, "s1")
    capture_event(store, {
        "type": "user_instruction", "session_id": "s1",
        "content": "Vamos usar PostgreSQL porque precisamos de transações ACID e schema previsível.",
        "files": ["src/db/schema.sql"],
    })
    report = make_engine(store).distill_session("s1")
    assert report.adrs == 1

    # session 3 asks about the database
    items = rank(store, CompileInput(query="qual banco de dados usar para transações?"), limit=5)
    assert any(i.entity.type == ArtifactType.ADR for i in items)
    adr = next(i.entity for i in items if i.entity.type == ArtifactType.ADR)
    assert "PostgreSQL" in adr.statement or "PostgreSQL" in adr.details.get("decision", "")


# ---------- criterion B: rejected alternative not re-recommended ----------

def test_B_rejected_alternative_surfaces_as_negative(store):
    sess(store, "s1")
    capture_event(store, {
        "type": "user_instruction", "session_id": "s1",
        "content": "Decidimos PostgreSQL em vez de MongoDB, porque MongoDB dá flexibilidade desnecessária.",
        "files": ["src/db/"],
    })
    make_engine(store).distill_session("s1")
    ctx = compile_context(store, CompileInput(query="escolher banco de dados", files=["src/db/"]))
    # the compiled context must warn about the rejected alternative
    assert "MongoDB" in ctx
    assert "rejected" in ctx.lower()


# ---------- criterion C: two similar fixes -> proposed correnda ----------

def test_C_recurring_root_cause_proposes_correnda(store):
    for sid, content, err in [
        ("s1", "Corrigido com guard clause e validação Pydantic porque payload externo não era validado",
         "TypeError: 'NoneType' object is not subscriptable"),
        ("s2", "Fix aplicado: adicionada validação Pydantic pois payload externo não era validado",
         "TypeError: payload malformed"),
    ]:
        sess(store, sid)
        capture_event(store, {"type": "error", "session_id": sid, "content": err,
                              "files": ["src/handlers/webhook_handler.py"]})
        capture_event(store, {"type": "agent_response", "session_id": sid, "content": content,
                              "files": ["src/handlers/webhook_handler.py"]})
    engine = make_engine(store)
    engine.distill_all()
    correndas = store.list_by_type(ArtifactType.CORRENDA)
    assert correndas, "expected a proposed correnda from two similar fixes"
    cor = correndas[0]
    assert cor.status == Status.PROPOSED, "correnda must be born proposed (ADR-C3)"
    assert cor.confidence >= 0.6
    origins = cor.details["origin"]
    assert len(origins) == 2
    # provenance: correnda traces back to both fixes
    for fix_id in origins:
        assert store.get(fix_id).type == ArtifactType.FIX


# ---------- criterion D: correnda only appears in relevant scope ----------

def test_D_scope_filtering(store):
    sess(store, "s1")
    capture_event(store, {"type": "error", "session_id": "s1",
                          "content": "TypeError: NoneType payload", "files": ["src/handlers/webhook.py"]})
    capture_event(store, {"type": "agent_response", "session_id": "s1",
                          "content": "Fix: validação Pydantic porque payload externo não era validado",
                          "files": ["src/handlers/webhook.py"]})
    sess(store, "s2")
    capture_event(store, {"type": "error", "session_id": "s2",
                          "content": "TypeError: payload malformed on retry", "files": ["src/handlers/webhook2.py"]})
    capture_event(store, {"type": "agent_response", "session_id": "s2",
                          "content": "Fix: validação Pydantic porque payload externo não era validado",
                          "files": ["src/handlers/webhook2.py"]})
    make_engine(store).distill_all()
    ctx_unrelated = compile_context(
        store, CompileInput(query="css styling do botão", files=["web/ui/button.css"]))
    ctx_related = compile_context(
        store, CompileInput(query="webhook payload", files=["src/handlers/webhook.py"]))
    assert "CORRENDA" in ctx_related.upper()
    assert "CORRENDA" not in ctx_unrelated.upper()


# ---------- criterion E: superseded memory does not dominate ----------

def test_E_superseded_stays_out_of_default_context(store):
    from cortex.storage.store import KnowledgeStore
    assert isinstance(store, KnowledgeStore)
    sess(store, "s1")
    capture_event(store, {"type": "user_instruction", "session_id": "s1",
                          "content": "Decidimos usar PostgreSQL porque precisamos de ACID.",
                          "files": ["src/db/"]})
    capture_event(store, {"type": "user_instruction", "session_id": "s1",
                          "content": "Decidimos usar Aurora Postgres em vez de PostgreSQL puro, porque gerenciado reduz operação.",
                          "files": ["src/db/"]})
    make_engine(store).distill_session("s1")
    adrs = store.list_by_type(ArtifactType.ADR)
    assert len(adrs) == 2
    old, new = sorted(adrs, key=lambda e: e.id)
    assert store.supersede(old.id, new.id)
    ctx = compile_context(store, CompileInput(query="banco de dados", files=["src/db/"]))
    assert new.details["decision"] in ctx
    assert old.details["decision"] not in ctx
    # history preserved (PRD §17.3)
    assert store.get(old.id).status == Status.SUPERSEDED
    assert store.get(old.id).superseded_by == new.id


# ---------- criterion F: memory traceable to evidence ----------

def test_F_why_traces_evidence(store):
    sess(store, "s1")
    capture_event(store, {"type": "user_instruction", "session_id": "s1",
                          "content": "Vamos usar PostgreSQL porque precisamos de ACID.",
                          "files": ["src/db/"]})
    make_engine(store).distill_session("s1")
    adr = store.list_by_type(ArtifactType.ADR)[0]
    p = adr.provenance
    assert p.source_session == "s1"
    assert p.source_events, "ADR must point to its source events"
    assert p.source_files == ["src/db/"]
    related = store.edges_of(src=adr.id)
    assert any(e["rel"] == "OCCURRED_IN" for e in related)


# ---------- criterion G: cortex failure must not block workflow ----------

def test_G_failure_returns_minimal_safe_context(store, tmp_path, monkeypatch):
    # corrupted ranking path -> minimal safe context, no exception
    class BrokenStore:
        def all_entities(self):
            raise RuntimeError("disk error")

        def list_by_type(self, _):
            return []

    ctx = compile_context(BrokenStore(), CompileInput(query="x"))
    assert ctx.startswith("<!-- CORTEX CONTEXT -->")
    assert "MINIMAL SAFE CONTEXT" in ctx

    # hook payload failure also degrades gracefully (workspace missing)
    import cortex.workspace as ws_mod
    from cortex.adapters.installer import handle_hook_payload
    monkeypatch.setattr(ws_mod, "detect_workspace", lambda start=None: None)
    result = handle_hook_payload({"hook_event_name": "SessionStart"}, tmp_path)
    assert result["ok"] is False


# ---------- criterion H: compiled context respects budget ----------

def test_H_budget_respected(store):
    sess(store, "s1")
    for i in range(15):
        capture_event(store, {
            "type": "user_instruction", "session_id": "s1",
            "content": f"Decidimos usar biblioteca número {i} porque precisamos de modularidade {i}.",
            "files": [f"src/mod{i}/"],
        })
    make_engine(store).distill_session("s1")
    small = compile_context(store, CompileInput(query="decisões do projeto"),
                            max_tokens=300)
    est = len(small) // 4
    assert est <= 320, f"context too large: ~{est} tokens for budget 300"
    assert small.startswith("<!-- CORTEX CONTEXT -->")
    assert small.rstrip().endswith("<!-- END CORTEX CONTEXT -->")


# ---------- redaction (PRD §25.2) ----------

def test_redaction_strips_secrets(store):
    sess(store, "s1")
    raw = "config with api_key = sk-proj-abc123def456ghi789jkl012 and password=SuperSecret9"
    capture_event(store, {"type": "user_instruction", "session_id": "s1", "content": raw})
    events = store.conn.execute("SELECT content FROM events").fetchall()
    contents = [r["content"] for r in events]
    assert any("sk-proj-abc123" not in (c or "") for c in contents)
    assert all("SuperSecret9" not in (c or "") for c in contents)


def test_redaction_allowlist_keeps_obvious_placeholders(store):
    """REFINAMENTO P2.4: illustrative examples aren't real secrets and
    shouldn't be nuked into <REDACTED>, degrading the stored evidence."""
    sess(store, "s1")
    raw = "see .env.example: password=changeme and api_key=your_api_key_here"
    capture_event(store, {"type": "user_instruction", "session_id": "s1", "content": raw})
    events = store.conn.execute("SELECT content FROM events").fetchall()
    contents = " ".join(r["content"] or "" for r in events)
    assert "changeme" in contents
    assert "your_api_key_here" in contents
    assert "<REDACTED>" not in contents


# ---------- session review (PRD §13.1) ----------

def test_session_review_counts(store):
    sess(store, "s1")
    capture_event(store, {"type": "user_instruction", "session_id": "s1",
                          "content": "Vamos usar Redis porque precisamos de cache rápido.",
                          "files": ["src/cache/"]})
    capture_event(store, {"type": "user_instruction", "session_id": "s1",
                          "content": "Ficou pendente: estratégia de invalidação de cache",
                          "files": []})
    make_engine(store).distill_session("s1")
    rev = build_session_review(store, "s1")
    assert rev is not None
    assert rev.details["produced"]["adrs"] == 1
    assert any("pendente" in u for u in rev.details["unresolved"])


# ---------- contradiction detection (PRD §17) ----------

def test_contradiction_edge_on_rejected_alternative(store):
    sess(store, "s1")
    capture_event(store, {"type": "user_instruction", "session_id": "s1",
                          "content": "Decidimos PostgreSQL em vez de MongoDB porque schema previsível.",
                          "files": ["src/db/"]})
    make_engine(store).distill_session("s1")
    sess(store, "s2")
    capture_event(store, {"type": "user_instruction", "session_id": "s2",
                          "content": "Vamos usar MongoDB para documentos porque flexibilidade ajuda.",
                          "files": ["src/db/"]})
    make_engine(store).distill_session("s2")
    edges = store.edges_of(rel="CONTRADICTS")
    assert edges, "new MongoDB decision should CONTRADICT the ADR that rejected it"


# ---------- hook adapter (PRD §6) ----------

def test_hook_payload_captures_session(tmp_path, project):
    from cortex.adapters.installer import handle_hook_payload
    payload = {
        "session_id": "sess-claude-001",
        "hook_event_name": "UserPromptSubmit",
        "prompt": "Vamos usar SQLite porque zero configuração.",
        "cwd": str(project),
    }
    result = handle_hook_payload(payload, project)
    assert result["ok"] is True
    s = KnowledgeStore(project / ".cortex" / "cortex.db")
    events = s.undistilled_events("sess-claude-001")
    assert events and events[0]["type"] == "user_instruction"
    s.close()


def test_hook_installs_claude_settings(project):
    from cortex.adapters.installer import install_hooks
    paths = install_hooks("claude-code", project)
    import json
    data = json.loads(paths[0].read_text(encoding="utf-8"))
    assert "SessionStart" in data["hooks"]


# ---------- retention (PRD §7.2 + Onda 1) ----------

def test_event_purge(store):
    sess(store, "s1")
    capture_event(store, {"type": "user_instruction", "session_id": "s1",
                          "content": "old undistilled event", "ts": "2020-01-01T00:00:00Z"})
    capture_event(store, {"type": "agent_response", "session_id": "s1",
                          "content": "old distilled event", "ts": "2020-01-01T00:00:01Z"})
    store.mark_distilled([e["id"] for e in store.undistilled_events("s1")
                          if e["content"] == "old distilled event"])
    # default: only distilled raw evidence is purged
    assert store.purge_old_events(days=30) == 1
    assert len(store.all_events("s1")) == 1  # undistilled candidate kept
    # explicit force purges everything older than the cutoff
    assert store.purge_old_events(days=30, only_distilled=False) == 1
    assert len(store.all_events("s1")) == 0


# ---------- hook CLI robustness (PRD §42: never block the workflow) ----------

def test_hook_cli_malformed_payload_does_not_crash(project):
    from typer.testing import CliRunner

    from cortex.cli.app import app as cli_app
    runner = CliRunner()
    result = runner.invoke(cli_app, ["hook", "--event", "claude-code"], input="not json {")
    assert result.exit_code == 0
    assert '"ok": false' in result.output
