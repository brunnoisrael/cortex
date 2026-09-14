"""Loader contracts: SWE-bench gate (Onda 2) and external control (Onda 4)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cortex.benchmarks.errors import SchemaError
from cortex.benchmarks.loaders.longmemeval import load_longmemeval
from cortex.benchmarks.loaders.swebench import load_swebench

SECRET_PATCH = "diff --git a/src/api.py SECRET_PATCH"
SECRET_TEST = "diff --git a/tests/api.py SECRET_TEST"


def _valid_row(**overrides):
    row = {
        "repo": "acme/widget",
        "instance_id": "widget-1",
        "base_commit": "abc123",
        "problem_statement": "Login fails when the session expires.",
        "patch": SECRET_PATCH,
        "test_patch": SECRET_TEST,
        "gold_evidence": ["src/api.py", "commit:abc123"],
        "normalized": {
            "schema": "cortex_memory_benchmark/v1",
            "id": "swe-widget-1",
            "source": "swebench",
            "source_revision": "abc123",
            "split": "dev",
            "domain": "software_project",
            "history": [
                {"session_id": "s0", "timestamp": "2026-01-01T00:00:00Z",
                 "events": [{"role": "user", "content": "Login fails after expiry.",
                             "timestamp": "2026-01-01T00:01:00Z"}]},
                {"session_id": "s1", "timestamp": "2026-01-02T00:00:00Z", "events": []},
            ],
            "cutoff": {"session_index": 1, "branch": "main"},
            "query": {"text": "login expiry"},
            "task_type": "exact_recall",
            "gold": {"expected_abstention": False, "gold_evidence": []},
            "constraints": {"max_context_tokens": 512, "allowed_future_data": False},
        },
    }
    row["normalized"]["checksums"] = {"history": "sha256:" + "0" * 64, "gold": "sha256:" + "0" * 64}
    row.update(overrides)
    return row


def _write(tmp_path: Path, rows: list[dict]) -> Path:
    path = tmp_path / "swe.json"
    path.write_text(json.dumps(rows), encoding="utf-8")
    return path


def test_swebench_normalizes_without_leaking_the_patch(tmp_path):
    from cortex.benchmarks.schema import Gold

    instances = load_swebench(_write(tmp_path, [_valid_row()]))
    assert len(instances) == 1
    instance = instances[0]
    assert instance.source == "swebench"
    assert instance.metadata["patch_excluded"] is True
    assert instance.metadata["repo"] == "acme/widget"
    # The adapter-visible projection (everything but gold) must be patch-free.
    projection = instance.model_copy(
        update={"gold": Gold(answer=None, expected_abstention=False, gold_evidence=[])}
    ).model_dump_json()
    assert SECRET_PATCH not in projection and SECRET_TEST not in projection


def test_swebench_gate_requires_cutoff_repo_and_both_patches(tmp_path):
    row = _valid_row()
    del row["base_commit"]
    with pytest.raises(SchemaError, match="base_commit"):
        load_swebench(_write(tmp_path, [row]))


def test_swebench_gate_refuses_a_row_without_a_test_patch(tmp_path):
    row = _valid_row()
    del row["test_patch"]
    with pytest.raises(SchemaError, match="test_patch"):
        load_swebench(_write(tmp_path, [row]))


def test_swebench_patch_is_gold_only_and_never_in_history(tmp_path):
    instance = load_swebench(_write(tmp_path, [_valid_row()]))[0]
    assert instance.gold.answer == SECRET_PATCH
    for session in instance.history:
        for event in session.events:
            assert SECRET_PATCH not in event.content and SECRET_TEST not in event.content


@pytest.mark.parametrize("kappa,expected", [(0.9, "confirmatory"), (0.3, "exploratory"), (None, "exploratory")])
def test_swebench_kappa_gate_decides_annotation_quality(tmp_path, kappa, expected):
    agreement = {"kappa": kappa} if kappa is not None else None
    instance = load_swebench(_write(tmp_path, [_valid_row(annotation_agreement=agreement)]))[0]
    assert instance.gold.annotation_quality == expected


def test_swebench_ordinal_scale_uses_the_lower_threshold(tmp_path):
    instance = load_swebench(_write(tmp_path, [_valid_row(
        annotation_agreement={"kappa": 0.55, "scale": "ordinal"})]))[0]
    assert instance.gold.annotation_quality == "confirmatory"


def test_longmemeval_is_loaded_as_an_exploratory_external_control(tmp_path):
    path = tmp_path / "lme.json"
    path.write_text(json.dumps({"data": [{
        "id": "lme-1", "domain": "general",
        "history": [{"session_id": "s0", "timestamp": "2026-01-01T00:00:00Z", "events": []}],
        "cutoff": {"session_index": 0, "branch": "main"},
        "query": {"text": "q"}, "task_type": "exact_recall",
        "gold": {"expected_abstention": False, "gold_evidence": []},
        "constraints": {"max_context_tokens": 64, "allowed_future_data": False},
        "checksums": {"history": "sha256:" + "0" * 64, "gold": "sha256:" + "0" * 64},
    }]}), encoding="utf-8")
    instances = load_longmemeval(path)
    assert instances[0].metadata["external_control"] is True
    assert instances[0].gold.annotation_quality == "exploratory"


def test_longmemeval_respects_a_human_annotation_agreement(tmp_path):
    path = tmp_path / "lme.json"
    row = {
        "id": "lme-2", "domain": "general",
        "history": [{"session_id": "s0", "timestamp": "2026-01-01T00:00:00Z", "events": []}],
        "cutoff": {"session_index": 0, "branch": "main"},
        "query": {"text": "q"}, "task_type": "exact_recall",
        "gold": {"expected_abstention": False, "gold_evidence": [],
                 "annotation_agreement": {"kappa": 0.8}},
        "constraints": {"max_context_tokens": 64, "allowed_future_data": False},
        "checksums": {"history": "sha256:" + "0" * 64, "gold": "sha256:" + "0" * 64},
    }
    path.write_text(json.dumps([row]), encoding="utf-8")
    assert load_longmemeval(path)[0].gold.annotation_quality == "confirmatory"
