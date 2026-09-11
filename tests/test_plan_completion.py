import json

from cortex.benchmarks.adapters import default_adapters
from cortex.benchmarks.extraction import evaluate_extraction
from cortex.engineering_review import build_review_summary, review_as_dict
from cortex.governance import promote
from cortex.knowledge.models import ArtifactType, Entity, EvidenceType, Provenance, Status
from cortex.portable import export_markdown, export_store, import_store, render_derived_rules
from cortex.storage.store import KnowledgeStore
from cortex.verification import verify_diff, verify_diff_apply, verify_entity


def test_portable_round_trip_keeps_external_knowledge_proposed(store, tmp_path):
    entity = Entity(
        id="adr-9000", type=ArtifactType.ADR, statement="Use PostgreSQL",
        status=Status.ACTIVE, scope=["src/db"],
        provenance=Provenance(extraction_source="test"),
    )
    store.upsert(entity)
    package_path = tmp_path / "cortex.json"
    export_store(store, package_path)
    clean = KnowledgeStore(tmp_path / "clean.db")
    try:
        result = import_store(clean, json.loads(package_path.read_text(encoding="utf-8")))
        assert result["imported"] == ["adr-9000"]
        assert clean.get("adr-9000").status == Status.PROPOSED
        assert "source of truth" in export_markdown(clean)
        assert "Derived Cortex rules" in render_derived_rules(clean)
    finally:
        clean.close()


def test_review_attach_and_human_confirmation_record_review_evidence(store, project):
    entity = Entity(
        id="adr-9001", type=ArtifactType.ADR, statement="Use PostgreSQL",
        status=Status.PROPOSED, scope=["src/db"],
        provenance=Provenance(extraction_source="test"),
    )
    store.upsert(entity)
    review = build_review_summary(store, project, paths=["src/db/schema.sql"], base="HEAD")
    assert entity.id in review.details["impacted_entities"]
    promoted = promote(store, entity.id, review_id=review.id, force_human=True)
    assert promoted.status == Status.ACTIVE
    assert any(item.type == EvidenceType.REVIEW for item in store.get(entity.id).evidence)
    assert review_as_dict(store, review.id)["affected"] == [entity.id]


def test_diff_check_is_read_only_then_apply_marks_changed_evidence_stale(store, project):
    path = project / "src" / "handlers" / "webhook_handler.py"
    entity = Entity(
        id="fix-9000", type=ArtifactType.FIX, statement="handle validates payload",
        status=Status.PROPOSED, scope=["src/handlers/webhook_handler.py"],
        provenance=Provenance(source_files=["src/handlers/webhook_handler.py"], extraction_source="test"),
    )
    store.upsert(entity)
    assert verify_entity(store, project, entity)["status"] == "verified"
    path.write_text("def handle(): return 'changed'\n", encoding="utf-8")
    read_only = verify_diff(store, project, "HEAD")
    assert read_only["read_only"] is True
    assert read_only["affected"][0]["verification"]["status"] == "stale"
    applied = verify_diff_apply(store, project, "HEAD")
    assert applied["affected"][0]["verification"]["status"] == "unverified"
    assert store.get(entity.id).freshness.stale is True


def test_evidence_refresh_preserves_event_provenance(store, project):
    store.add_event({"id": "evt-proof", "type": "user_instruction", "content": "Use handle"})
    entity = Entity(
        id="fix-9001", type=ArtifactType.FIX, statement="handle validates payload",
        status=Status.PROPOSED, scope=["src/handlers/webhook_handler.py"],
        provenance=Provenance(source_events=["evt-proof"], source_files=["src/handlers/webhook_handler.py"]),
    )
    store.upsert(entity)
    result = verify_entity(store, project, entity)
    assert result["status"] == "verified"
    assert any(item.type == EvidenceType.EVENT and item.location == "evt-proof"
               for item in store.get(entity.id).evidence)


def test_read_only_diff_fingerprints_directory_evidence(store, project):
    entity = Entity(
        id="fix-9002", type=ArtifactType.FIX, statement="handle validates payload",
        status=Status.PROPOSED, scope=["src/handlers"],
        provenance=Provenance(source_files=["src/handlers"], extraction_source="test"),
    )
    store.upsert(entity)
    assert verify_entity(store, project, entity)["status"] == "verified"
    (project / "src" / "handlers" / "webhook_handler.py").write_text("def handle(): return 'changed'\n", encoding="utf-8")
    result = verify_diff(store, project, "HEAD")
    assert result["affected"]
    assert result["affected"][0]["verification"]["status"] == "stale"


def test_extraction_metrics_and_external_adapters_are_explicit(project, store):
    corpus = [
        {"id": "one", "events": [{"id": "e", "type": "user_instruction",
          "content": "Vamos usar PostgreSQL porque precisamos de ACID", "files": []}],
         "expected": [{"type": "adr", "contains": "PostgreSQL"}]},
    ]
    result = evaluate_extraction(corpus)
    assert "adr" in result["metrics"]
    adapters = default_adapters(store)
    assert set(adapters) >= {"cortex", "agent_memory_engine", "agent_memory_bridge", "basic_memory", "native_host"}
    assert adapters["agent_memory_engine"].evaluate([], k=5).available is False
