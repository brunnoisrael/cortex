"""The real Cortex pipeline under benchmark conditions (Onda 1).

These tests exercise the shipping store, distillation, temporal policy,
ranking and compilation — not a stand-in.  Each case gets an ephemeral store,
so a test that observes state from another case is a real failure.
"""

from __future__ import annotations

import pytest

from cortex.benchmarks.adapters import CortexAdapter
from cortex.benchmarks.metrics import (
    case_metrics,
    extraction_recall,
    extraction_spurious_rate,
    recall_at_k,
    set_f1,
)
from cortex.benchmarks.schema import instance_from_dict

from .corpora_cases import build_case

# Representative conversations, built with the same generator that commits the
# corpus, so a test failure means the pipeline changed and not the fixture.
TRACKING, DELETION, ABSENCE = "mem-tracking-api", "mem-deletion-logs", "mem-absence-provider"
AGGREGATION, CASCADE, NEGATION = "mem-aggregation-ci", "mem-cascade-auth", "adv-contradiction-open"


def _run(case_id: str, **flags):
    raw = build_case(case_id)
    instance = instance_from_dict(raw, materialize=True)
    return instance, CortexAdapter(**flags).run(instance)


def test_supersession_promotes_the_latest_statement():
    instance, result = _run(TRACKING)
    assert result.selected == ["s1:0"]
    assert result.trace["superseded_ids"], "the earlier decision must be invalidated"
    assert case_metrics(result, instance)["current_state_accuracy"] == 1.0
    assert case_metrics(result, instance)["stale_leak_rate"] == 0.0


def test_explicit_negation_invalidates_the_earlier_assertion():
    """An unresolved contradiction must not resurface the superseded plan."""
    instance, result = _run(NEGATION)
    metrics = case_metrics(result, instance)
    assert instance.gold.invalid_entities == ["s0:0"]
    assert "s0:0" not in result.selected, "the contradicted plan leaked back into the context"
    assert metrics["stale_leak_rate"] == 0.0
    assert metrics["current_state_accuracy"] == 1.0


def test_abstains_when_history_has_no_evidence_for_the_query():
    instance, result = _run(ABSENCE)
    assert result.abstained is True
    assert result.missing_evidence, "abstention without missing evidence is not acceptable"
    assert case_metrics(result, instance)["false_certainty_rate"] == 0.0


def test_aggregation_recovers_the_whole_set():
    instance, result = _run(AGGREGATION)
    assert set(result.selected) == set(instance.gold.current_entities)
    assert set_f1(result, instance) == 1.0


def test_extraction_is_measured_independently_from_ranking():
    instance, result = _run(TRACKING)
    # Distillation saw both decisions...
    assert set(instance.gold.gold_evidence) <= set(result.trace["extracted_ids"])
    assert extraction_recall(result, instance) == 1.0
    # ...and the ranking still had to pick the current one for this query.
    assert result.selected == ["s1:0"]
    assert recall_at_k(result.retrieved, instance.gold.current_entities, 5) == 1.0


def test_extraction_spurious_rate_counts_distilled_noise():
    instance, result = _run(ABSENCE)
    extracted = set(result.trace["extracted_ids"])
    assert extraction_spurious_rate(result, instance) == len(extracted - set(instance.gold.gold_evidence)) / len(extracted)


def test_cascade_lineage_reaches_the_dependent_knowledge():
    instance, result = _run(CASCADE)
    assert result.trace["lineage_ids"], "a supersession must record its lineage"
    metrics = case_metrics(result, instance)
    assert metrics["cascade_correctness_hop1"] == 1.0
    # Hop 2: the dependent knowledge that references the superseded subject.
    assert set(instance.gold.gold_evidence) & set(result.trace["hop2_ids"])


def test_dedup_no_longer_absorbs_a_state_update():
    """Regression test for the gap documented in docs/adr/2026-09-13-memory-
    benchmark-waves.md (case ``adv-dedup-absorbs-update``).

    Root cause (traced, see cortex/distillation/extractors.py
    ``short_identifier_tokens``): ``statement_tokens`` drops <=2-char tokens,
    so "s3-artifacts" and "s3-artifacts-v2" tokenized to the same set and
    ``_find_duplicate`` merged them at similarity 1.0 — absorbing the state
    update into one entity instead of letting ``_apply_temporal_policy``
    (which runs after ``distill_all`` and already has its own
    ``_same_subject`` check at ``SUPERSESSION_SIMILARITY = 0.5``) supersede
    the old one.

    NOTE: these expected values were derived by tracing the code path, not by
    running this test — pydantic could not be installed in the environment
    that authored this patch (network egress disabled), so
    ``cortex.knowledge.models`` could not be imported. Run this test before
    merging. If it fails, the actual entity count / metric values printed by
    the failure tell you exactly where the traced prediction and the real
    pipeline diverge — likely either scope propagation into ``Entity.scope``
    or an interaction with another ablation flag.
    """
    instance, result = _run("adv-dedup-absorbs-update")
    metrics = case_metrics(result, instance)
    assert result.trace["extraction"]["entities"] == 2, (
        "dedup should no longer merge the two near-identical statements into one entity"
    )
    assert metrics["deletion_compliance"] == 1.0, (
        "the superseded s3-artifacts entity must now be excluded from the gold-current set"
    )
    assert metrics["stale_leak_rate"] == 0.0, (
        "the old bucket name must no longer leak into the answer once supersession runs"
    )


@pytest.mark.parametrize("flag", CortexAdapter.ABLATION_FLAGS)
def test_each_ablation_is_runnable_in_isolation(flag):
    instance, baseline = _run(TRACKING)
    _, ablated = _run(TRACKING, **{flag: True})
    assert ablated.trace["flags"][flag] is True
    assert sum(ablated.trace["flags"].values()) == 1
    assert baseline.trace["flags"][flag] is False


def test_disabling_supersession_lets_obsolete_state_through():
    _, baseline = _run(TRACKING)
    _, ablated = _run(TRACKING, disable_supersession=True)
    assert set(ablated.selected) - set(baseline.selected), (
        "without the temporal filter the superseded decision must reappear"
    )


def test_disabling_the_evidence_ledger_loses_provenance():
    _, baseline = _run(TRACKING)
    _, ablated = _run(TRACKING, disable_evidence_ledger=True)
    assert baseline.evidence
    assert ablated.evidence == []


def test_authority_ablation_changes_the_relative_weight_of_sources():
    """Ablating authority must remove the authority factor from every score."""
    raw = build_case(TRACKING)
    # A commit-sourced decision carries OBSERVED authority (0.65) while a user
    # statement carries HUMAN_CONFIRMED (1.0).
    raw["history"][0]["events"].append({
        "role": "commit", "files": ["src/api"],
        "content": "Vamos usar a biblioteca requests para o cliente HTTP interno.",
        "timestamp": "2026-01-05T10:05:00Z",
    })
    instance = instance_from_dict(build_case(TRACKING) | {"history": raw["history"]}, materialize=True)
    baseline = CortexAdapter().run(instance)
    ablated = CortexAdapter(disable_authority=True).run(instance)
    assert len(baseline.trace["entity_ids"]) >= 2
    assert ablated.trace["scores"] != baseline.trace["scores"]
    # score = rest * authority_weight, so removing the factor can only raise
    # the score (weights are <= 1); anything else means the ablation moved a
    # different signal.
    for entity_id, ablated_score in ablated.trace["scores"].items():
        assert ablated_score >= baseline.trace["scores"][entity_id]


def test_token_budget_is_respected_exactly():
    instance, result = _run(TRACKING)
    assert result.trace["compile"]["estimated_context_tokens"] <= instance.constraints.max_context_tokens
    assert set(result.tokens) >= {"input", "retrieved", "compiled"}


def test_future_event_never_reaches_the_store():
    raw = build_case(TRACKING)
    raw["history"][0]["events"][0]["timestamp"] = "2030-01-01T00:00:00Z"
    instance = instance_from_dict(raw, materialize=True)
    with pytest.raises(Exception, match="future event"):
        CortexAdapter().run(instance)


def test_no_state_leaks_between_cases():
    adapter = CortexAdapter()
    adapter.run(instance_from_dict(build_case(TRACKING), materialize=True))
    other = instance_from_dict(build_case(ABSENCE), materialize=True)
    result = adapter.run(other)
    assert result.trace["superseded_ids"] == [], "state from the previous case must not carry over"
    assert result.trace["extraction"]["entities"] <= len(other.history)
