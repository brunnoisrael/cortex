"""Regression tests for PLANO_ENDURECIMENTO_2026-09-08.md item 5.3:

- ALTERNATIVE_RE no longer fires on any bare "over <word>", only on an
  actual "prefer X over Y" construction.
- review.py's unresolved-marker detection no longer flags ordinary
  Portuguese words ("todos", "método") that happen to contain "todo" as a
  substring.
- distillation extractors work in English, not just Portuguese (the
  acceptance suite in test_acceptance.py was PT-only before this)."""

from __future__ import annotations

from cortex.capture.recorder import capture_event
from cortex.compiler.compiler import CompileInput, rank
from cortex.config import CortexConfig
from cortex.distillation.engine import DistillationEngine
from cortex.distillation.extractors import extract_decisions
from cortex.distillation.review import build_session_review
from cortex.knowledge.models import ArtifactType
from cortex.storage.store import KnowledgeStore


def make_engine(store: KnowledgeStore) -> DistillationEngine:
    cfg = CortexConfig()
    return DistillationEngine(store, min_confidence=cfg.min_confidence_for_persistence,
                              correnda_min_evidence=cfg.correnda_min_evidence)


def sess(store: KnowledgeStore, sid: str) -> None:
    store.ensure_session(sid, host="test")


# ---------- ALTERNATIVE_RE: no false "rejected alternative" from bare "over" ----------

def test_alternative_re_does_not_fire_on_unrelated_over():
    events = [{
        "id": "e1", "type": "user_instruction",
        "content": "We decided to use Redis for caching. "
                    "We'll go over configuration details in the next meeting.",
    }]
    candidates = extract_decisions(events)
    assert len(candidates) == 1
    assert candidates[0].details.get("alternatives_rejected") in (None, []), (
        "bare 'over <word>' with no 'prefer ... over' construction must not "
        "be read as a rejected alternative"
    )


def test_alternative_re_fires_on_prefer_x_over_y():
    events = [{
        "id": "e1", "type": "user_instruction",
        "content": "We decided to use Redis. We prefer Redis over Memcached "
                    "for the richer data structures.",
    }]
    candidates = extract_decisions(events)
    assert len(candidates) == 1
    assert "Memcached" in candidates[0].details.get("alternatives_rejected", [])


# ---------- review.py: "todo" only matches the real code-comment marker ----------

def test_review_does_not_flag_todos_as_unresolved(store):
    sess(store, "s1")
    capture_event(store, {
        "type": "agent_response", "session_id": "s1",
        "content": "Prontinho, todos os testes passaram e o método ficou mais simples.",
    })
    review = build_session_review(store, "s1")
    assert review is not None
    assert review.details["unresolved"] == [], (
        "'todos'/'método' contain 'todo' as a substring but are not an "
        "unresolved code TODO"
    )


def test_review_flags_real_todo_marker_as_unresolved(store):
    sess(store, "s1")
    capture_event(store, {
        "type": "agent_response", "session_id": "s1",
        "content": "Implementei o handler. // TODO: adicionar validação de payload.",
    })
    review = build_session_review(store, "s1")
    assert review is not None
    assert len(review.details["unresolved"]) == 1


# ---------- EN fixture parity: acceptance criterion A, in English ----------

def test_acceptance_A_in_english(store):
    """Mirrors test_acceptance.py's criterion A, but entirely in English —
    the extractors' PT patterns were the only ones exercised by the
    acceptance suite before this."""
    sess(store, "s1")
    capture_event(store, {
        "type": "user_instruction", "session_id": "s1",
        "content": "We decided to use PostgreSQL because we need ACID "
                    "transactions and a predictable schema.",
        "files": ["src/db/schema.sql"],
    })
    report = make_engine(store).distill_session("s1")
    assert report.adrs == 1

    items = rank(store, CompileInput(query="which database for transactions?"), limit=5)
    assert any(i.entity.type == ArtifactType.ADR for i in items)
    adr = next(i.entity for i in items if i.entity.type == ArtifactType.ADR)
    assert "PostgreSQL" in adr.statement or "PostgreSQL" in adr.details.get("decision", "")
