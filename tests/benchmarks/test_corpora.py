"""Corpus integrity: the committed corpora must match their generator (Onda 0/1)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cortex.benchmarks.corpora.build_internal import (
    ADVERSARIAL_CASES,
    CASES,
    REVISION,
    write_corpora,
)
from cortex.benchmarks.loaders.meme import stratify
from cortex.benchmarks.manifest import endpoint_table_digest
from cortex.benchmarks.schema import instance_from_dict, validate_checksums

from .corpora_cases import build_case

CORPORA = Path("cortex/benchmarks/corpora")
TASK_TYPES = {"exact_recall", "aggregation", "tracking", "deletion", "cascade", "absence"}


def _rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


@pytest.mark.parametrize("relative", [
    "normalized/engineering_memory_v1.nofiller.jsonl",
    "normalized/engineering_memory_v1.filler32k.jsonl",
    "normalized/mvp_v1.jsonl",
    "adversarial/superseded_abstention.jsonl",
])
def test_every_committed_case_is_a_valid_v1_instance(relative):
    for raw in _rows(CORPORA / relative):
        instance = instance_from_dict(dict(raw))
        validate_checksums(instance)
        assert instance.checksums.history.startswith("sha256:")
        assert instance.constraints.allowed_future_data is False


def test_committed_files_match_the_builder_byte_for_byte():
    before = {path: path.read_bytes() for path in sorted(CORPORA.rglob("*")) if path.suffix in {".jsonl", ".json"}}
    write_corpora()
    for path, content in before.items():
        assert path.read_bytes() == content, f"{path} is out of date; run the corpus builder"


def test_internal_corpus_covers_every_pre_registered_task_type():
    assert {case["task_type"] for case in CASES} == TASK_TYPES
    assert {case["split"] for case in CASES} >= {"dev", "eval", "regression"}


def test_gold_is_derivable_from_the_visible_history_only():
    for case in [*CASES, *ADVERSARIAL_CASES]:
        built = build_case(case["id"])
        history = built["history"][: built["cutoff"]["session_index"]]
        visible = {f"{session['session_id']}:{index}"
                   for session in history for index in range(len(session["events"]))}
        gold = built["gold"]
        assert set(gold["current_entities"]) <= visible, case["id"]
        assert set(gold["invalid_entities"]) <= visible, case["id"]
        assert set(gold["gold_evidence"]) <= visible, case["id"]
        # The cutoff boundary session is empty and post-cutoff: it must never
        # be referenced by gold.
        boundary = built["history"][built["cutoff"]["session_index"]]
        assert boundary["events"] == [], case["id"]


def test_events_never_occur_after_the_cutoff():
    for case in [*CASES, *ADVERSARIAL_CASES]:
        built = build_case(case["id"])
        cutoff = built["history"][built["cutoff"]["session_index"]]["timestamp"]
        for session in built["history"][: built["cutoff"]["session_index"]]:
            assert session["timestamp"] <= cutoff, case["id"]
            for event in session["events"]:
                assert event["timestamp"] <= cutoff, case["id"]


def test_filler_variant_only_adds_noise_and_keeps_gold_stable():
    for case in CASES:
        plain, filled = build_case(case["id"]), build_case(case["id"], filler="filler32k")
        assert filled["gold"] == plain["gold"]
        assert len(filled["history"]) > len(plain["history"])
        assert filled["id"] != plain["id"]
        # No gold event id may shift because of the filler.
        assert {session["session_id"] for session in plain["history"]} <= {
            session["session_id"] for session in filled["history"]}


def test_filler_variant_adds_a_realistic_token_load():
    from cortex.compiler.compiler import token_estimate

    filled = build_case("mem-tracking-api", filler="filler32k")
    tokens = sum(token_estimate(event["content"])
                 for session in filled["history"] for event in session["events"])
    assert tokens > 10_000, "the filler variant must be a real noise load, not a token or two"


def test_stratification_reports_the_sample_composition():
    instances = [instance_from_dict(build_case(case["id"])) for case in CASES]
    table = stratify(instances)
    assert set(table) == {"task_type", "hop", "history_size", "filler"}
    assert sum(table["task_type"].values()) == len(CASES)
    assert table["filler"] == {"nofiller": len(CASES)}


def test_manifest_pins_the_frozen_endpoint_table():
    document = json.loads((CORPORA / "manifests/memory_v1.json").read_text(encoding="utf-8"))
    assert document["expected_endpoint_digest"] == endpoint_table_digest()
    assert document["dataset_revisions"] == {"internal": REVISION}
    assert document["network_enabled"] is False
    assert document["corpus_hash"].startswith("sha256:")
