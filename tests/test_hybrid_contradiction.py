"""Tests for Hybrid Search with Density & Revalidation, and Multi-Vector Semantic Contradictions."""

from pathlib import Path

import pytest

from cortex.compiler.compiler import CompileInput, content_density, rank
from cortex.distillation.engine import DistillationEngine, DistillationReport
from cortex.distillation.extractors import (
    dense_semantic_similarity,
    detect_negation_conflict,
)
from cortex.knowledge.models import ArtifactType, Authority, Entity, Provenance, Status
from cortex.storage.store import KnowledgeStore


@pytest.fixture
def store(tmp_path: Path) -> KnowledgeStore:
    db_path = tmp_path / "cortex.db"
    st = KnowledgeStore(db_path)
    yield st
    st.close()


def test_dense_semantic_similarity_and_content_density():
    # Paraphrase matching
    sim = dense_semantic_similarity("banco relacional postgresql", "usaremos postgresql para persistência de dados")
    assert sim > 0.25


    # Content density
    density_high = content_density("src/db/schema.sql TypeError in handle_auth_middleware")
    density_low = content_density("vamos fazer algo simples aqui")
    assert density_high > density_low


test_negation_data = [
    ("Usar PostgreSQL em vez de MongoDB", "Não usar PostgreSQL em produção", True),
    ("Ativar cache em memória", "Desativar cache em memória", True),
    ("Usar PostgreSQL para dados", "Decidimos PostgreSQL em vez de MySQL", False),
]

@pytest.mark.parametrize("text_a,text_b,expected", test_negation_data)
def test_detect_negation_conflict(text_a, text_b, expected):
    assert detect_negation_conflict(text_a, text_b) == expected


def test_hybrid_search_ranks_dense_and_density_boosted_entities(store: KnowledgeStore):
    e1 = Entity(
        id="adr-0001",
        type=ArtifactType.ADR,
        statement="Decidimos usar PostgreSQL para ter suporte a ACID e integridade referencial",
        status=Status.ACTIVE,
        authority=Authority.HUMAN_CONFIRMED,
        confidence=0.90,
        scope=["src/db"],
        details={"decision": "PostgreSQL"},
        provenance=Provenance(source_session="sess-1"),
    )
    e2 = Entity(
        id="adr-0002",
        type=ArtifactType.ADR,
        statement="Decidimos usar SQLite em arquivo local para testes unitários isolados",
        status=Status.ACTIVE,
        authority=Authority.AGENT_INFERRED,
        confidence=0.75,
        scope=["tests"],
        details={"decision": "SQLite"},
        provenance=Provenance(source_session="sess-1"),
    )
    store.upsert(e1)
    store.upsert(e2)

    # Add edges to e1 to increase graph density
    store.add_edge(e1.id, "OCCURRED_IN", "sess-1")
    store.add_edge(e1.id, "AFFECTS", "file:src/db/schema.py")
    store.add_edge(e1.id, "EVIDENCED_BY", "commit-abc1234")

    # Search with natural language query matching paraphrases
    items = rank(store, CompileInput(query="banco de dados relacional postgres", files=["src/db"]))
    assert len(items) >= 1
    assert items[0].entity.id == "adr-0001"
    assert items[0].reasons["dense"] > 0.1
    assert items[0].reasons["graph_density"] > 0.0


def test_revalidation_phase_penalizes_contradicted_entities(store: KnowledgeStore):
    e1 = Entity(
        id="adr-0001",
        type=ArtifactType.ADR,
        statement="Usar PostgreSQL como banco primário",
        status=Status.ACTIVE,
        authority=Authority.HUMAN_CONFIRMED,
        confidence=0.95,
        scope=["src/db"],
        details={"decision": "PostgreSQL"},
        provenance=Provenance(source_session="sess-1"),
    )
    e2 = Entity(
        id="adr-0002",
        type=ArtifactType.ADR,
        statement="Não usar PostgreSQL, migrar para MongoDB",
        status=Status.ACTIVE,
        authority=Authority.AGENT_INFERRED,
        confidence=0.70,
        scope=["src/db"],
        details={"decision": "MongoDB"},
        provenance=Provenance(source_session="sess-2"),
    )
    store.upsert(e1)
    store.upsert(e2)

    # Record CONTRADICTS edge from e2 pointing to e1 (or e1 contradicts e2)
    store.add_edge(e2.id, "CONTRADICTS", e1.id)

    items = rank(store, CompileInput(query="banco de dados", files=["src/db"]))
    reasons_by_id = {i.entity.id: i.reasons for i in items}
    assert "adr-0001" in reasons_by_id
    assert reasons_by_id["adr-0001"]["contradicted"] is True


def test_multi_vector_contradiction_matrix_in_engine(store: KnowledgeStore):
    # Vector 1: ADR vs Rejected Alternative
    adr1 = Entity(
        id="adr-0001",
        type=ArtifactType.ADR,
        statement="Decidimos PostgreSQL em vez de MongoDB",
        status=Status.ACTIVE,
        authority=Authority.HUMAN_CONFIRMED,
        confidence=0.90,
        scope=["src/db"],
        details={"decision": "PostgreSQL", "alternatives_rejected": ["MongoDB"]},
        provenance=Provenance(source_session="sess-1"),
    )
    adr2 = Entity(
        id="adr-0002",
        type=ArtifactType.ADR,
        statement="Decidimos usar MongoDB para flexibilidade de documentos",
        status=Status.CANDIDATE,
        authority=Authority.AGENT_INFERRED,
        confidence=0.75,
        scope=["src/db"],
        details={"decision": "MongoDB"},
        provenance=Provenance(source_session="sess-2"),
    )
    store.upsert(adr1)
    store.upsert(adr2)

    engine = DistillationEngine(store)
    rep = DistillationReport()
    engine._detect_contradictions(rep)

    assert rep.contradictions >= 1
    edges = store.edges_of(rel="CONTRADICTS")
    assert len(edges) >= 1
