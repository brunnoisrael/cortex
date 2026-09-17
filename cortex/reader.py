"""Deterministic reader for compiled Cortex context.

The reader is deliberately unable to access a store, raw history, or gold
answers.  Its only memory input is the rendered context block, which makes
the evidence-to-response boundary auditable and reproducible.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from cortex.compiler.compiler import keyword_overlap

Support = Literal["supported", "partial", "unsupported"]

_EVIDENCE_LINE = re.compile(r"^\s*-\s+\[([^\]\s]+)\]\s+(.*)$")
_OBSOLETE = re.compile(r"\b(?:status\s*:\s*)?(?:superseded|stale|deleted)\b", re.IGNORECASE)


class ReaderClaim(BaseModel):
    """One answer claim and the context IDs that support it."""

    model_config = ConfigDict(extra="forbid")

    claim: str
    evidence_ids: list[str] = Field(default_factory=list)
    support: Support
    support_score: float = Field(ge=0.0, le=1.0)


class ReaderResponse(BaseModel):
    """Auditable final response produced from compiled context only."""

    model_config = ConfigDict(extra="forbid")

    schema_: Literal["cortex_reader_response/v1"] = Field(
        "cortex_reader_response/v1", alias="schema"
    )
    status: Literal["answer", "abstention"]
    answer: str | None = None
    claims: list[ReaderClaim] = Field(default_factory=list)
    cited_evidence_ids: list[str] = Field(default_factory=list)
    abstained: bool
    abstention_reason: str | None = None
    missing_evidence: list[str] = Field(default_factory=list)
    trace: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_evidence_contract(self) -> ReaderResponse:
        """Require every emitted claim to be backed by compiled-context IDs."""
        if self.abstained != (self.status == "abstention"):
            raise ValueError("status and abstained must agree")
        context_ids = set(self.trace.get("context_evidence_ids", []))
        obsolete_ids = set(self.trace.get("obsolete_evidence_ids", []))
        cited_ids = set(self.cited_evidence_ids)
        claim_ids = {evidence_id for claim in self.claims for evidence_id in claim.evidence_ids}
        eligible_ids = context_ids - obsolete_ids
        if not cited_ids <= eligible_ids or not claim_ids <= eligible_ids:
            raise ValueError("citations must refer to current evidence IDs in compiled context")
        if cited_ids != claim_ids:
            raise ValueError("cited evidence IDs must match claim evidence IDs")
        if not self.abstained:
            if not self.answer or not self.claims or not cited_ids:
                raise ValueError("a supported answer requires claims and evidence citations")
            if any(claim.support != "supported" for claim in self.claims):
                raise ValueError("a supported answer cannot contain unsupported claims")
        return self


def _context_evidence(context: str) -> tuple[list[tuple[str, str]], list[str]]:
    """Extract bracketed evidence lines and IDs without consulting anything else."""
    evidence: list[tuple[str, str]] = []
    obsolete: list[str] = []
    for line in context.splitlines():
        match = _EVIDENCE_LINE.match(line)
        if not match:
            continue
        evidence_id, text = match.groups()
        if _OBSOLETE.search(text):
            obsolete.append(evidence_id)
            continue
        evidence.append((evidence_id, text.strip()))
    return evidence, obsolete


def read_compiled_context(
    query: str,
    compiled_context: str,
    *,
    support_threshold: float = 0.25,
) -> ReaderResponse:
    """Read only ``compiled_context`` and cite only IDs present in it.

    The fixed policy is intentionally conservative: a candidate below the
    lexical support threshold is reported as partial evidence and produces an
    abstention instead of a confident answer.  Superseded/stale/deleted lines
    are never answerable in the default current-state mode.
    """
    if not isinstance(query, str) or not isinstance(compiled_context, str):
        raise TypeError("query and compiled_context must be strings")
    if not 0.0 < support_threshold <= 1.0:
        raise ValueError("support_threshold must be in (0, 1]")

    evidence, obsolete_ids = _context_evidence(compiled_context)
    context_ids = [evidence_id for evidence_id, _ in evidence] + obsolete_ids
    scored = [
        (keyword_overlap(query, text), evidence_id, text)
        for evidence_id, text in evidence
    ]
    scored.sort(key=lambda row: (-row[0], context_ids.index(row[1])))
    base_trace = {
        "schema": "compiled_context_trace/v1",
        "context_evidence_ids": list(context_ids),
        "obsolete_evidence_ids": list(obsolete_ids),
        "support_threshold": support_threshold,
        "query": query,
    }

    if not scored:
        return ReaderResponse(
            status="abstention",
            abstained=True,
            abstention_reason=(
                "only_obsolete_evidence" if obsolete_ids else "no_cited_evidence_in_compiled_context"
            ),
            missing_evidence=[query] if query.strip() else ["relevant evidence"],
            trace={**base_trace, "selected_evidence_ids": [], "max_support": 0.0},
        )

    score, evidence_id, text = scored[0]
    support: Support = "supported" if score >= support_threshold else "partial" if score > 0 else "unsupported"
    claim = ReaderClaim(
        claim=text,
        evidence_ids=[evidence_id],
        support=support,
        support_score=round(score, 4),
    )
    if support != "supported":
        return ReaderResponse(
            status="abstention",
            claims=[claim],
            cited_evidence_ids=[evidence_id],
            abstained=True,
            abstention_reason="insufficient_factual_support",
            missing_evidence=[query] if query.strip() else ["sufficient factual support"],
            trace={
                **base_trace,
                "selected_evidence_ids": [evidence_id],
                "max_support": round(score, 4),
            },
        )

    return ReaderResponse(
        status="answer",
        answer=text,
        claims=[claim],
        cited_evidence_ids=[evidence_id],
        abstained=False,
        trace={
            **base_trace,
            "selected_evidence_ids": [evidence_id],
            "max_support": round(score, 4),
        },
    )


def reader_metrics(response: ReaderResponse | Mapping[str, Any], instance: Any) -> dict[str, float]:
    """Evaluate reader dimensions separately from retrieval metrics."""
    if not isinstance(response, ReaderResponse):
        response = ReaderResponse.model_validate(response)
    context_ids = set(response.trace.get("context_evidence_ids", []))
    cited = set(response.cited_evidence_ids)
    citations_valid = bool(cited <= context_ids) and all(
        set(claim.evidence_ids) <= context_ids for claim in response.claims
    )
    if response.abstained:
        support_factual = float(bool(response.missing_evidence))
        fidelity = 1.0 if response.status == "abstention" and citations_valid else 0.0
    else:
        support_factual = float(
            bool(response.claims)
            and all(claim.support == "supported" and claim.evidence_ids for claim in response.claims)
            and bool(cited)
            and citations_valid
        )
        fidelity = support_factual

    expected_abstention = bool(instance.gold.expected_abstention)
    abstention_accuracy = float(response.abstained == expected_abstention)
    answer = (response.answer or "").casefold()
    accepted = [str(value).casefold() for value in (instance.gold.accepted_answers or [])]
    matches_gold = bool(answer) and (
        any(value in answer for value in accepted)
        if accepted
        else keyword_overlap(str(instance.gold.answer or ""), answer) >= 0.25
    )
    final_accuracy = float(response.abstained if expected_abstention else (not response.abstained and matches_gold))
    return {
        "reader_support_factual": support_factual,
        "reader_fidelity": fidelity,
        "reader_abstention_accuracy": abstention_accuracy,
        "reader_final_response_accuracy": final_accuracy,
        "reader_citation_validity": float(citations_valid),
    }


__all__ = ["ReaderClaim", "ReaderResponse", "read_compiled_context", "reader_metrics"]
