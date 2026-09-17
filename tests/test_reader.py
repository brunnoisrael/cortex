"""Adversarial regression tests for the compiled-context reader."""

from __future__ import annotations

import pytest

from cortex.reader import ReaderResponse, read_compiled_context


def test_reader_answers_only_with_a_cited_context_id():
    response = read_compiled_context(
        "qual banco usar para transações",
        "<!-- CORTEX CONTEXT -->\n- [ev-db] O banco para transações é PostgreSQL.\n",
    )

    assert response.status == "answer"
    assert response.abstained is False
    assert response.cited_evidence_ids == ["ev-db"]
    assert response.claims[0].evidence_ids == ["ev-db"]
    assert set(response.cited_evidence_ids) <= set(response.trace["context_evidence_ids"])


def test_reader_abstains_for_absence_and_reports_missing_evidence():
    response = read_compiled_context(
        "qual banco usar para transações",
        "<!-- CORTEX CONTEXT -->\n- [ev-ui] A interface web usa React.\n",
    )

    assert response.status == "abstention"
    assert response.abstained is True
    assert response.abstention_reason == "insufficient_factual_support"
    assert response.missing_evidence == ["qual banco usar para transações"]
    assert response.claims[0].support in {"partial", "unsupported"}


def test_reader_rejects_obsolete_evidence_for_current_state():
    response = read_compiled_context(
        "qual banco usar",
        "<!-- CORTEX CONTEXT -->\n- [ev-old] O banco era Redis (status: superseded)\n",
    )

    assert response.abstained is True
    assert response.abstention_reason == "only_obsolete_evidence"
    assert response.cited_evidence_ids == []
    assert response.trace["obsolete_evidence_ids"] == ["ev-old"]


def test_reader_never_accepts_a_forged_citation():
    response = read_compiled_context(
        "banco PostgreSQL",
        "<!-- CORTEX CONTEXT -->\n- [ev-db] O banco é PostgreSQL.\n",
    )

    assert "forged" not in response.cited_evidence_ids
    assert set(response.cited_evidence_ids) <= {"ev-db"}


def test_reader_is_byte_reproducible_for_same_input():
    context = "<!-- CORTEX CONTEXT -->\n- [ev-db] O banco é PostgreSQL.\n"
    first = read_compiled_context("banco PostgreSQL", context).model_dump_json()
    second = read_compiled_context("banco PostgreSQL", context).model_dump_json()
    assert first == second


def test_reader_response_rejects_forged_or_uncited_claims():
    with pytest.raises(ValueError, match="compiled context"):
        ReaderResponse(
            status="answer",
            answer="O banco é PostgreSQL.",
            claims=[
                {
                    "claim": "O banco é PostgreSQL.",
                    "evidence_ids": ["ev-forged"],
                    "support": "supported",
                    "support_score": 1.0,
                }
            ],
            cited_evidence_ids=["ev-forged"],
            abstained=False,
            trace={"context_evidence_ids": ["ev-real"]},
        )


def test_reader_response_rejects_answer_without_citation():
    with pytest.raises(ValueError, match="requires claims"):
        ReaderResponse(
            status="answer",
            answer="Uma resposta sem evidência.",
            abstained=False,
            trace={"context_evidence_ids": ["ev-real"]},
        )


def test_reader_response_rejects_resurrecting_obsolete_citation():
    with pytest.raises(ValueError, match="current evidence"):
        ReaderResponse(
            status="answer",
            answer="O banco é Redis.",
            claims=[
                {
                    "claim": "O banco é Redis.",
                    "evidence_ids": ["ev-old"],
                    "support": "supported",
                    "support_score": 1.0,
                }
            ],
            cited_evidence_ids=["ev-old"],
            abstained=False,
            trace={
                "context_evidence_ids": ["ev-old"],
                "obsolete_evidence_ids": ["ev-old"],
            },
        )
