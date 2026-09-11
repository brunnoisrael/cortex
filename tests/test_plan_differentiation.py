import json

from cortex.compiler.compiler import CompileInput, retrieval_trace
from cortex.governance import promote, review_queue
from cortex.knowledge.evidence import export_evidence_package
from cortex.knowledge.models import (
    ArtifactType,
    Entity,
    Evidence,
    EvidenceStatus,
    EvidenceType,
    ReviewPolicy,
    RiskLevel,
    Status,
)


def _entity(store, entity_id="adr-0001", status=Status.PROPOSED):
    entity = Entity(
        id=entity_id, type=ArtifactType.ADR, statement="Usar PostgreSQL para transações",
        status=status, risk_level=RiskLevel.MEDIUM,
        review_policy=ReviewPolicy.MULTIPLE_EVIDENCE,
        scope=["src/db"],
    )
    store.upsert(entity)
    return entity


def test_evidence_ledger_round_trip_and_export(store, tmp_path):
    entity = _entity(store)
    store.add_evidence(entity.id, Evidence(
        id="ev-1", type=EvidenceType.FILE, location="src/db/schema.py",
        fingerprint="sha256:abc", status=EvidenceStatus.RESOLVED,
        verification_method="ast",
    ))
    loaded = store.get(entity.id)
    assert loaded is not None
    assert loaded.evidence[0].fingerprint == "sha256:abc"
    package = export_evidence_package(store, entity.id, tmp_path / "audit.json")
    assert package["cortex_schema"] == "evidence_ledger/v1"
    assert json.loads((tmp_path / "audit.json").read_text())["evidence"][0]["status"] == "resolved"


def test_governance_promotion_is_policy_checked_and_idempotent(store):
    entity = _entity(store)
    store.add_evidence(entity.id, Evidence(
        id="ev-1", type=EvidenceType.FILE, location="a.py", fingerprint="sha256:a",
        status=EvidenceStatus.RESOLVED,
    ))
    store.add_evidence(entity.id, Evidence(
        id="ev-2", type=EvidenceType.TEST, location="test_a.py", fingerprint="sha256:b",
        status=EvidenceStatus.RESOLVED,
    ))
    promote(store, entity.id, reason="two independent checks")
    promote(store, entity.id, reason="same operation")
    assert store.get(entity.id).status == Status.ACTIVE
    assert len(store.governance_receipts(entity.id)) == 1


def test_review_queue_contains_proposals_and_trace_explains_exclusions(store):
    entity = _entity(store)
    trace = retrieval_trace(store, CompileInput(query="transações"), budget=100)
    assert entity.id in trace["eligible_ids"]
    assert any(row["id"] == entity.id for row in trace["ranked"])
    assert entity in review_queue(store)

