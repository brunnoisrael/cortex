"""Testes unitários para o gerador de perguntas e o conversor de sessões.

Cobre:
- test_converter_produces_valid_v1_instances
- test_converter_materializes_correct_checksums
- test_min_questions_per_session_is_ten
- test_no_duplicate_questions_per_type_and_theme
- test_all_task_types_represented_in_dogfooding_corpus
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent.parent
DEV_DIR = REPO_ROOT / "cortex" / "dev"
SESSION_FILE = DEV_DIR / "sessions" / "20260915_evidence_integrity_dogfooding.json"
ANNOTATIONS_FILE = DEV_DIR / "annotations" / "20260915_evidence_integrity_dogfooding_annotations.json"
CORPUS_FILE = REPO_ROOT / "cortex" / "benchmarks" / "corpora" / "normalized" / "dogfooding_v1.jsonl"


@pytest.fixture(scope="module")
def session() -> dict:
    return json.loads(SESSION_FILE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def annotations() -> list[dict]:
    return json.loads(ANNOTATIONS_FILE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def corpus_instances() -> list[dict]:
    """Lê o corpus JSONL gerado pelo conversor."""
    assert CORPUS_FILE.exists(), (
        f"Corpus não encontrado: {CORPUS_FILE}. "
        "Execute `python -m cortex.dev.session_to_benchmark` primeiro."
    )
    return [json.loads(line) for line in CORPUS_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# C5.1 — Conversor produz instâncias v1 válidas
# ---------------------------------------------------------------------------

def test_converter_produces_valid_v1_instances(corpus_instances: list[dict]) -> None:
    """Todas as instâncias do corpus devem ser válidas pelo schema v1."""
    from cortex.benchmarks.schema import instance_from_dict

    assert len(corpus_instances) >= 1, "Corpus está vazio"
    errors = []
    for raw in corpus_instances:
        try:
            instance_from_dict(raw)
        except Exception as exc:
            errors.append(f"{raw.get('id', '?')}: {exc}")

    assert not errors, "Instâncias inválidas:\n" + "\n".join(errors)


# ---------------------------------------------------------------------------
# C5.2 — Checksums materializados corretamente
# ---------------------------------------------------------------------------

def test_converter_materializes_correct_checksums(corpus_instances: list[dict]) -> None:
    """Os checksums de cada instância devem bater com o conteúdo real."""
    from cortex.benchmarks.schema import instance_from_dict, validate_checksums

    for raw in corpus_instances:
        instance = instance_from_dict(raw)
        try:
            validate_checksums(instance)
        except Exception as exc:
            pytest.fail(f"Checksum inválido para {instance.id}: {exc}")


# ---------------------------------------------------------------------------
# C5.3 — Mínimo de 10 perguntas por sessão
# ---------------------------------------------------------------------------

def test_min_questions_per_session_is_ten(session: dict) -> None:
    """O gerador deve produzir pelo menos 10 perguntas para a sessão de dogfooding."""
    from cortex.dev.validation_questions import generate_validation_questions

    questions = generate_validation_questions(session)
    assert len(questions) >= 10, (
        f"Esperado >= 10 perguntas, obtido {len(questions)}. "
        f"Tipos gerados: {[q['question_type'] for q in questions]}"
    )


# ---------------------------------------------------------------------------
# C5.4 — Sem duplicatas por (question_type, chave)
# ---------------------------------------------------------------------------

def test_no_duplicate_questions_per_type_and_theme(session: dict) -> None:
    """Não deve haver dois question_ids iguais numa mesma sessão."""
    from cortex.dev.validation_questions import generate_validation_questions

    questions = generate_validation_questions(session)
    ids = [q["question_id"] for q in questions]
    duplicates = [qid for qid in ids if ids.count(qid) > 1]
    assert not duplicates, f"IDs duplicados: {set(duplicates)}"


# ---------------------------------------------------------------------------
# C5.5 — Todos os task_types relevantes cobertos no corpus
# ---------------------------------------------------------------------------

def test_all_task_types_represented_in_dogfooding_corpus(corpus_instances: list[dict]) -> None:
    """O corpus deve cobrir exact_recall, aggregation, tracking e cascade.

    Absence e deletion são mapeados para aggregation/exact_recall com
    expected_abstention=True — verificamos que há pelo menos 3 instâncias
    com abstention para cobrir esses casos.
    """
    task_types_found = {inst["task_type"] for inst in corpus_instances}
    required = {"exact_recall", "aggregation", "tracking", "cascade"}
    missing = required - task_types_found
    assert not missing, f"task_types ausentes no corpus: {missing}"

    # Verificar casos de abstention (absence + deletion mapeados)
    abstention_cases = [i for i in corpus_instances if i["gold"]["expected_abstention"]]
    assert len(abstention_cases) >= 3, (
        f"Esperado >= 3 casos de abstention (absence/deletion), obtido {len(abstention_cases)}"
    )


# ---------------------------------------------------------------------------
# C5.6 — Anotações têm >=20 entradas cobrindo os 6 question_types
# ---------------------------------------------------------------------------

def test_annotations_cover_all_question_types(annotations: list[dict]) -> None:
    """As anotações manuais devem cobrir os 6 question_types planejados."""
    assert len(annotations) >= 20, (
        f"Esperado >= 20 anotações, obtido {len(annotations)}"
    )
    types_found = {a["question_type"] for a in annotations}
    required = {"exact_recall", "aggregation", "tracking", "cascade", "absence", "deletion"}
    missing = required - types_found
    assert not missing, f"question_types ausentes nas anotações: {missing}"
