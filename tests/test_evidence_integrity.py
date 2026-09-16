"""Tests for evidence ID generation and storage integrity (IntegrityError prevention)."""

from pathlib import Path
import tempfile
import pytest

from cortex.distillation.engine import DistillationEngine
from cortex.distillation.extractors import Candidate
from cortex.knowledge.evidence import evidence_id, resolve_entity_evidence
from cortex.knowledge.models import (
    ArtifactType,
    Entity,
    Evidence,
    EvidenceStatus,
    EvidenceType,
    Provenance,
    ReviewPolicy,
    RiskLevel,
    Status,
    _utcnow,
)
from cortex.storage.store import KnowledgeStore


@pytest.fixture
def temp_store():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_store.db"
        store = KnowledgeStore(db_path)
        yield store
        store.close()


def test_multiple_entities_sharing_event(temp_store):
    """Multiple entities derived from the exact same event must not collide in evidence table."""
    temp_store.ensure_session("sess-1", host="test")
    temp_store.add_event({
        "id": "evt-shared-1",
        "type": "user_instruction",
        "session_id": "sess-1",
        "content": "Use PostgreSQL for metadata and SQLite for local cache",
    })

    engine = DistillationEngine(temp_store, llm="heuristic", network_calls=False)

    cand1 = Candidate(
        statement="Use PostgreSQL for metadata",
        etype=ArtifactType.ADR,
        details={},
        scope=[],
        source="explicit_user_statement",
        event_ids=["evt-shared-1"],
        session_id="sess-1",
    )
    cand2 = Candidate(
        statement="Use SQLite for local cache",
        etype=ArtifactType.ADR,
        details={},
        scope=[],
        source="explicit_user_statement",
        event_ids=["evt-shared-1"],
        session_id="sess-1",
    )

    # Persisting both candidates must succeed without sqlite3.IntegrityError
    ent1 = engine._persist_candidate(cand1)
    ent2 = engine._persist_candidate(cand2)

    assert ent1.id != ent2.id
    ev1 = temp_store.list_evidence(ent1.id)
    ev2 = temp_store.list_evidence(ent2.id)

    assert len(ev1) >= 1
    assert len(ev2) >= 1
    assert ev1[0].id != ev2[0].id
    assert ev1[0].location == "evt-shared-1"
    assert ev2[0].location == "evt-shared-1"


def test_candidate_with_duplicate_event_ids(temp_store):
    """Candidate with duplicate event IDs in cand.event_ids must be handled cleanly."""
    temp_store.ensure_session("sess-2", host="test")
    temp_store.add_event({
        "id": "evt-dup-1",
        "type": "agent_response",
        "session_id": "sess-2",
        "content": "Configured database connection pool",
    })

    engine = DistillationEngine(temp_store, llm="heuristic", network_calls=False)

    cand = Candidate(
        statement="Configured database connection pool",
        etype=ArtifactType.FIX,
        details={},
        scope=[],
        source="explicit_fix",
        event_ids=["evt-dup-1", "evt-dup-1", "evt-dup-1"],
        session_id="sess-2",
    )

    ent = engine._persist_candidate(cand)
    evidence = temp_store.list_evidence(ent.id)
    assert len(evidence) == 1
    assert evidence[0].location == "evt-dup-1"


def test_evidence_id_handles_empty_and_none_locations():
    """evidence_id must never crash and must produce distinct hashes with extra discriminator."""
    id1 = evidence_id("ent-1", EvidenceType.FILE, "")
    id2 = evidence_id("ent-1", EvidenceType.FILE, None)
    assert id1 == id2
    assert id1.startswith("ev-")

    # With extra discriminator
    id3 = evidence_id("ent-1", EvidenceType.FILE, "", extra="turn-0")
    id4 = evidence_id("ent-1", EvidenceType.FILE, "", extra="turn-1")
    assert id3 != id4
    assert id3.startswith("ev-")
    assert id4.startswith("ev-")


def test_resolve_entity_evidence_deduplication(temp_store):
    """resolve_entity_evidence must deduplicate empty, repeated, or multiple sources."""
    temp_store.ensure_session("sess-3", host="test")
    temp_store.add_event({
        "id": "evt-res-1",
        "type": "user_instruction",
        "session_id": "sess-3",
        "content": "Testing evidence resolution",
    })

    entity = Entity(
        id="ent-test-res",
        type=ArtifactType.ADR,
        statement="Always use UTF-8 encoding",
        status=Status.ACTIVE,
        risk_level=RiskLevel.LOW,
        review_policy=ReviewPolicy.MULTIPLE_EVIDENCE,
        observed_at=_utcnow(),
        scope=["", "   ", "README.md", "README.md"],
        details={"affected_files": ["README.md", "", "   "], "tests": ["test.py", "test.py"]},
        provenance=Provenance(
            source_events=["evt-res-1", "evt-res-1"],
            source_files=["README.md", "README.md"],
        ),
    )

    with tempfile.TemporaryDirectory() as repo_dir:
        (Path(repo_dir) / "README.md").write_text("Always use UTF-8 encoding", encoding="utf-8")
        results = resolve_entity_evidence(temp_store, Path(repo_dir), entity)
        result_ids = [e.id for e in results]
        # No duplicate IDs in results
        assert len(result_ids) == len(set(result_ids))


def test_store_upsert_evidence_idempotency(temp_store):
    """KnowledgeStore.upsert must be strictly idempotent even with duplicate evidence objects."""
    ev = Evidence(
        id="ev-manual-1",
        type=EvidenceType.EVENT,
        location="evt-1",
        status=EvidenceStatus.RESOLVED,
    )
    entity = Entity(
        id="ent-idem-1",
        type=ArtifactType.ADR,
        statement="Idempotency test entity",
        status=Status.ACTIVE,
        risk_level=RiskLevel.LOW,
        review_policy=ReviewPolicy.MULTIPLE_EVIDENCE,
        observed_at=_utcnow(),
        evidence=[ev, ev],  # duplicate in memory list
    )

    # First upsert must deduplicate and succeed
    temp_store.upsert(entity)
    loaded = temp_store.list_evidence("ent-idem-1")
    assert len(loaded) == 1

    # Second upsert must succeed cleanly (no SQLite UNIQUE constraint failure)
    temp_store.upsert(entity)
    loaded2 = temp_store.list_evidence("ent-idem-1")
    assert len(loaded2) == 1
