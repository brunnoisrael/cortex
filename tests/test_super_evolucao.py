"""Tests for Cortex SUPER Evolução (Ondas 6 to 12 + MCP P(-1))."""

from __future__ import annotations

from cortex.benchmarks.ccb import format_report, run_ccb, run_ccb_on_store
from cortex.commons import export_common_pattern, import_common_pattern
from cortex.compiler.compiler import CompileInput, compile_context, rank
from cortex.knowledge.models import (
    ArtifactType,
    Authority,
    Entity,
    Provenance,
    Status,
    session_id_for,
)
from cortex.server.mcp_server import cortex_emit
from cortex.storage.store import KnowledgeStore
from cortex.verification import verify_entity
from cortex.visualizer import (
    export_provenance_graph_file,
    generate_provenance_graph_html,
)


def test_onda6_mcp_cortex_emit(project, store, monkeypatch):
    monkeypatch.setenv("CORTEX_ROOT", str(project))
    
    # Emit an ADR
    res_adr = cortex_emit(
        kind="adr",
        statement="Use Pydantic for API schema validation",
        rationale="Prevents payload type errors at endpoint boundary",
        alternatives_rejected=["marshmallow", "dataclasses"],
        scope=["src/api/"],
        confidence_self_reported=0.95,
    )
    assert "emitted" in res_adr
    assert "adr" in res_adr
    
    # Emit a Correnda (Negative Knowledge)
    res_cor = cortex_emit(
        kind="correnda",
        statement="Do not bypass Pydantic validation when parsing webhooks",
        rationale="Unvalidated webhook payloads caused production outages",
        scope=["src/webhooks/"],
        confidence_self_reported=0.90,
    )
    assert "emitted" in res_cor
    assert "correnda" in res_cor

    entities = store.all_entities()
    assert len(entities) >= 2
    
    adr_item = [e for e in entities if e.type == ArtifactType.ADR][0]
    assert adr_item.statement == "Use Pydantic for API schema validation"
    assert adr_item.provenance.extraction_source == "cortex_emit_mcp_tool"
    assert adr_item.authority == Authority.AGENT_INFERRED
    assert adr_item.status == Status.PROPOSED
    assert adr_item.details["alternatives_rejected"] == ["marshmallow", "dataclasses"]

    # Verify context compiler includes directive
    ctx = compile_context(store, CompileInput(query="validation"))
    assert "[DIRECTIVE]" in ctx


def test_onda7_ast_tier0_verification(project, store):
    # Create Python scope file with AST structures
    api_file = project / "src" / "api" / "handlers.py"
    api_file.parent.mkdir(parents=True, exist_ok=True)
    api_file.write_text(
        "import pydantic\n\n"
        "class WebhookHandler:\n"
        "    def validate_payload(self, data):\n"
        "        return pydantic.model_validate(data)\n",
        encoding="utf-8",
    )

    ent = Entity(
        id=store.reserve_entity_id(ArtifactType.CORRENDA),
        type=ArtifactType.CORRENDA,
        statement="Use pydantic model_validate for WebhookHandler payloads",
        status=Status.PROPOSED,
        authority=Authority.AGENT_INFERRED,
        confidence=0.85,
        scope=["src/api/handlers.py"],
        session_id=session_id_for("test"),
        details={"rule": "Use pydantic model_validate"},
        provenance=Provenance(extraction_source="test"),
    )
    store.upsert(ent)

    result = verify_entity(store, project, ent)
    assert result["status"] == "verified"
    assert result["authority"] == Authority.REPOSITORY_VERIFIED.value
    assert result["verification_source"] == "ast"

    # Verify rank applies AST boost
    items = rank(store, CompileInput(query="pydantic payload"))
    assert len(items) > 0
    assert items[0].reasons["ast_verified"] is True


def test_onda8_ccb_benchmark_execution(store):
    # 1. Run fixture benchmark
    report_fixture = run_ccb()
    assert report_fixture["tasks_passed"] > 0
    assert "tasks_total" in report_fixture

    # 2. Run dogfood benchmark on active store
    report_dogfood = run_ccb_on_store(store)
    assert "tasks_passed" in report_dogfood
    
    formatted = format_report(report_fixture)
    assert "CCB (memory-quality subset)" in formatted


def test_onda9_visual_provenance_graph(project, store):
    ent1 = Entity(
        id=store.reserve_entity_id(ArtifactType.ADR),
        type=ArtifactType.ADR,
        statement="Use SQLite for local storage",
        status=Status.ACTIVE,
        authority=Authority.HUMAN_CONFIRMED,
        confidence=0.98,
        scope=["cortex/storage/"],
        session_id=session_id_for("test"),
        details={"decision": "SQLite"},
        provenance=Provenance(extraction_source="test"),
    )
    store.upsert(ent1)

    html_str = generate_provenance_graph_html(store, focus_id=ent1.id)
    assert "<!DOCTYPE html>" in html_str
    assert "Cortex Knowledge Provenance Graph" in html_str
    assert ent1.id in html_str

    output_path = project / "cortex_graph.html"
    export_provenance_graph_file(store, output_path, focus_id=ent1.id)
    assert output_path.exists()
    assert output_path.stat().st_size > 500


def test_onda10_correnda_commons(store):
    ent = Entity(
        id=store.reserve_entity_id(ArtifactType.CORRENDA),
        type=ArtifactType.CORRENDA,
        statement="Validate external payload with secret token sk_live_12345 in src/secret_handler.py",
        status=Status.ACTIVE,
        authority=Authority.HUMAN_CONFIRMED,
        confidence=0.90,
        scope=["src/secret_handler.py"],
        session_id=session_id_for("test"),
        details={"rule": "Validate external payload", "rationale": "Prevent unauthorized access"},
        provenance=Provenance(extraction_source="test"),
    )
    store.upsert(ent)

    # Export common pattern (must redact secret token and sanitize scope)
    pattern = export_common_pattern(store, ent.id)
    assert pattern["cortex_schema"] == "correnda_commons/v1"
    assert "sk_live_12345" not in pattern["statement"]
    assert "secret_handler.py" in pattern["generalized_scope"]

    # Import common pattern into store
    imported_ent = import_common_pattern(store, pattern)
    assert imported_ent.id != ent.id
    assert imported_ent.authority == Authority.AGENT_INFERRED
    assert imported_ent.status == Status.PROPOSED
    assert imported_ent.details["origin"] == ["correnda_commons"]


def test_onda11_federation_read_only(tmp_path, store):
    # Create secondary store
    sec_db = tmp_path / "sec_cortex.db"
    store_sec = KnowledgeStore(sec_db)
    
    ent_sec = Entity(
        id=store_sec.reserve_entity_id(ArtifactType.ADR),
        type=ArtifactType.ADR,
        statement="Shared org standard: OAuth2 JWT authentication",
        status=Status.ACTIVE,
        authority=Authority.HUMAN_CONFIRMED,
        confidence=0.95,
        scope=["auth/"],
        session_id=session_id_for("federated"),
        details={"decision": "OAuth2 JWT"},
        provenance=Provenance(extraction_source="federated_repo"),
    )
    store_sec.upsert(ent_sec)

    # Rank using primary store + federated secondary store
    items = rank(store, CompileInput(query="OAuth2 JWT"), federated_stores=[store_sec])
    assert len(items) == 1
    assert items[0].entity.id == ent_sec.id
    assert items[0].reasons["federated"] is True

    store_sec.close()


def test_onda12_autocalibration_weights(store):
    ent = Entity(
        id=store.reserve_entity_id(ArtifactType.ADR),
        type=ArtifactType.ADR,
        statement="Architecture tuning test entity",
        status=Status.ACTIVE,
        authority=Authority.HUMAN_CONFIRMED,
        confidence=0.90,
        scope=["src/core/"],
        session_id=session_id_for("test"),
        details={"decision": "tuning"},
        provenance=Provenance(extraction_source="test"),
    )
    store.upsert(ent)

    # Compare default rank score vs custom weights override
    items_default = rank(store, CompileInput(query="tuning test"))
    items_custom = rank(
        store,
        CompileInput(query="tuning test"),
        weights_override={"authority": 2.0, "freshness": 1.5},
    )

    assert len(items_default) == 1
    assert len(items_custom) == 1
    assert items_custom[0].score > items_default[0].score
