"""Freeze gates: pinned revisions, pinned endpoints and corpus drift (Onda 0)."""

from __future__ import annotations

from pathlib import Path

import pytest

from cortex.benchmarks.errors import AmbiguityError, SchemaError
from cortex.benchmarks.manifest import (
    RunManifest,
    assert_declared_revisions,
    assert_endpoint_table,
    endpoint_table_digest,
    freeze_corpus,
    select_split,
)
from cortex.benchmarks.runner import corpus_path, run_benchmark

from .helpers import make_case, raw_case

MANIFEST = Path("cortex/benchmarks/corpora/manifests/memory_v1.json")


def _manifest(**overrides):
    payload = {
        "cortex_version": "0.1.0", "python_version": "3.11", "os": "portable", "hardware": "portable",
        "tokenizer": "whitespace/v1", "embedding_model": "none", "embedding_version": "none",
        "embedding_cache_dir": "outside-repo", "seed": 0, "retry_policy": "off",
        "network_enabled": False, "evidence_classification": "exploratory",
        "corpus_hash": "sha256:" + "0" * 64,
        "dataset_revisions": {"internal": "test"},
    }
    payload.update(overrides)
    return RunManifest.model_validate(payload)


def test_frozen_corpus_records_split_and_revision_per_case():
    instances = [make_case("a"), make_case("b", task_type="deletion", split="eval")]
    frozen = freeze_corpus(instances)
    assert frozen.splits == {"eval": ["b"], "regression": ["a"]}
    assert frozen.revisions == {"internal": "test"}
    assert set(frozen.case_hashes) == {"a", "b"}
    assert frozen.corpus_hash.startswith("sha256:")


def test_content_hash_changes_when_observable_input_changes():
    before = freeze_corpus([make_case("a")]).case_hashes["a"]
    after = freeze_corpus([make_case("a", query="SQLite")]).case_hashes["a"]
    assert before != after


def test_mixed_revisions_in_one_source_are_rejected():
    instances = [make_case("a"), make_case("b")]
    instances[1] = instances[1].model_copy(update={"source_revision": "other"})
    with pytest.raises(SchemaError, match="mixes revisions"):
        freeze_corpus(instances)


def test_undeclared_revision_blocks_the_run():
    instances = [make_case("a")]
    manifest = _manifest(dataset_revisions={})
    with pytest.raises(SchemaError, match="does not declare revisions"):
        assert_declared_revisions(manifest, instances)


def test_endpoint_digest_pins_the_pre_registered_table():
    assert_endpoint_table(_manifest(expected_endpoint_digest=endpoint_table_digest()))
    with pytest.raises(AmbiguityError, match="without an ADR"):
        assert_endpoint_table(_manifest(expected_endpoint_digest="sha256:" + "1" * 64))


def test_split_selection_never_returns_an_empty_run():
    instances = [make_case("a", split="dev"), make_case("b", split="eval")]
    assert [item.id for item in select_split(instances, ["dev"])] == ["a"]
    assert [item.id for item in select_split(instances, None)] == ["a", "b"]
    with pytest.raises(SchemaError, match="no cases match"):
        select_split(instances, ["regression"])


def test_corrupting_the_corpus_file_is_detected_as_drift(tmp_path):
    from cortex.benchmarks.schema import instance_from_dict

    corpus = tmp_path / "corpus.jsonl"
    frozen = instance_from_dict(raw_case("case-1"), materialize=True)
    corpus.write_text(_json_line(frozen.model_dump(by_alias=True, mode="json")), encoding="utf-8")
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(_manifest_document(corpus), encoding="utf-8")

    run_benchmark(manifest_path, ["bm25"], tmp_path / "out")
    changed = instance_from_dict(raw_case("case-1", query="SQLite"), materialize=True)
    corpus.write_text(_json_line(changed.model_dump(by_alias=True, mode="json")), encoding="utf-8")
    with pytest.raises(Exception, match="corpus hash drift"):
        run_benchmark(manifest_path, ["bm25"], tmp_path / "out2")


def test_manifest_resolves_a_relative_corpus_path():
    manifest = _manifest(corpus="../normalized/engineering_memory_v1.nofiller.jsonl")
    resolved = corpus_path(manifest, MANIFEST)
    assert resolved is not None and resolved.name == "engineering_memory_v1.nofiller.jsonl"


def _json_line(raw: dict) -> str:
    import json

    return json.dumps(raw) + "\n"


def _manifest_document(corpus: Path) -> str:
    import hashlib
    import json

    payload = {
        "schema": "cortex_memory_benchmark_manifest/v1", "cortex_version": "0.1.0",
        "python_version": "3.11", "os": "portable", "hardware": "portable",
        "tokenizer": "whitespace/v1", "embedding_model": "none", "embedding_version": "none",
        "embedding_cache_dir": "outside-repo", "seed": 0, "retry_policy": "off",
        "network_enabled": False, "evidence_classification": "exploratory",
        "corpus_hash": "sha256:" + hashlib.sha256(corpus.read_bytes()).hexdigest(),
        "dataset_revisions": {"internal": "test"}, "corpus": corpus.name,
    }
    return json.dumps(payload)
