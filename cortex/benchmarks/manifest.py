"""Reproducibility manifest and deterministic environment metadata."""

from __future__ import annotations

import hashlib
import json
import platform
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from .errors import AmbiguityError, SchemaError
from .schema import BenchmarkInstance, _BenchmarkModel

PRIMARY_ENDPOINTS = {
    "exact_recall": ("recall_at_k", "evidence_resolution_rate"),
    "aggregation": ("set_f1", "scope_accuracy"),
    "tracking": ("current_state_accuracy", "supersession_accuracy"),
    "deletion": ("deletion_compliance", "stale_leak_rate"),
    "cascade": ("cascade_correctness_hop1", "lineage_completeness"),
    "absence": ("abstention_recall", "false_certainty_rate"),
}


def endpoint_table_digest() -> str:
    """Hash of the pre-registered primary endpoints (plan §4).

    A manifest may pin this digest; drifting from it is a specification change
    and requires an ADR, so it must fail loudly instead of silently moving the
    goalposts between runs.
    """
    payload = {task: list(endpoints) for task, endpoints in sorted(PRIMARY_ENDPOINTS.items())}
    return "sha256:" + hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


class FrozenCorpus(_BenchmarkModel):
    """Content freeze of a run's inputs (plan §12, gate G0)."""

    schema_: str = Field("cortex_memory_benchmark_freeze/v1", alias="schema")
    corpus_hash: str
    case_hashes: dict[str, str] = Field(default_factory=dict)
    splits: dict[str, list[str]] = Field(default_factory=dict)
    revisions: dict[str, str] = Field(default_factory=dict)


class RunManifest(_BenchmarkModel):
    schema_: str = Field("cortex_memory_benchmark_manifest/v1", alias="schema")
    cortex_version: str
    python_version: str
    os: str
    hardware: str
    tokenizer: str
    embedding_model: str
    embedding_version: str
    embedding_cache_dir: str
    evidence_classification: Literal["confirmatory", "exploratory"]
    seed: int
    retry_policy: Literal["deterministic", "off"] = "off"
    network_enabled: Literal[False] = False
    corpus_hash: str
    dataset_revisions: dict[str, str] = Field(default_factory=dict)
    expected_endpoint_digest: str | None = None
    splits: list[str] | None = None
    corpus: str | None = None
    cases: list[dict[str, Any]] | None = None
    frozen: FrozenCorpus | None = None


def case_content_hash(instance: BenchmarkInstance) -> str:
    """Stable hash of everything an adapter may observe plus its gold.

    Two runs of the same corpus must produce the same value; a changed value
    means the frozen input changed and results are no longer comparable.
    """
    payload = instance.model_dump(by_alias=True, mode="json")
    payload.pop("checksums", None)
    return "sha256:" + hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def freeze_corpus(instances: list[BenchmarkInstance]) -> FrozenCorpus:
    if not instances:
        raise SchemaError("cannot freeze an empty corpus")
    splits: dict[str, list[str]] = defaultdict(list)
    revisions: dict[str, str] = {}
    case_hashes: dict[str, str] = {}
    for instance in instances:
        case_hashes[instance.id] = case_content_hash(instance)
        splits[instance.split].append(instance.id)
        previous = revisions.get(instance.source)
        if previous is not None and previous != instance.source_revision:
            raise SchemaError(
                f"{instance.source} mixes revisions {previous!r} and {instance.source_revision!r}; "
                "a run must pin one revision per source"
            )
        revisions[instance.source] = instance.source_revision
    return FrozenCorpus(
        corpus_hash=corpus_digest(case_hashes),
        case_hashes=dict(sorted(case_hashes.items())),
        splits={name: sorted(ids) for name, ids in sorted(splits.items())},
        revisions=dict(sorted(revisions.items())),
    )


def corpus_digest(case_hashes: dict[str, str]) -> str:
    payload = json.dumps(case_hashes, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def assert_declared_revisions(manifest: RunManifest, instances: list[BenchmarkInstance]) -> None:
    """Fail when the corpus carries a revision the manifest did not declare."""
    observed = freeze_corpus(instances).revisions
    declared = {key: str(value) for key, value in manifest.dataset_revisions.items()}
    missing = {source: rev for source, rev in observed.items() if source not in declared}
    if missing:
        raise SchemaError(f"manifest does not declare revisions for sources {sorted(missing)}")
    mismatched = {source: (declared[source], rev) for source, rev in observed.items() if declared[source] != rev}
    if mismatched:
        detail = ", ".join(f"{source}: declared {d!r} != corpus {r!r}" for source, (d, r) in sorted(mismatched.items()))
        raise SchemaError(f"dataset revision mismatch ({detail})")


def assert_endpoint_table(manifest: RunManifest) -> None:
    if manifest.expected_endpoint_digest is None:
        return
    if manifest.expected_endpoint_digest != endpoint_table_digest():
        raise AmbiguityError(
            "primary endpoints changed without an ADR: manifest pins "
            f"{manifest.expected_endpoint_digest}, code has {endpoint_table_digest()}"
        )


def select_split(instances: list[BenchmarkInstance], splits: list[str] | None) -> list[BenchmarkInstance]:
    if not splits:
        return list(instances)
    wanted = set(splits)
    selected = [item for item in instances if item.split in wanted]
    if not selected:
        raise SchemaError(f"no cases match requested splits {sorted(wanted)}")
    return selected


def freeze_seed(seed: int) -> None:
    random.seed(seed)
    try:
        import numpy as np

        np.random.seed(seed)
    except ImportError:
        pass


def corpus_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest(path: Path) -> RunManifest:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if "corpus" in raw and not Path(raw["corpus"]).is_absolute():
        raw["corpus"] = str((path.parent / raw["corpus"]).resolve())
    return RunManifest.model_validate(raw)


def environment_manifest(*, corpus: Path, seed: int = 0, corpus_file: str | None = None) -> RunManifest:
    from cortex import __version__

    return RunManifest(
        cortex_version=__version__, python_version=sys.version.split()[0], os=platform.platform(),
        hardware=platform.machine(), tokenizer="whitespace/v1", embedding_model="none",
        embedding_version="none", embedding_cache_dir="outside-repository", seed=seed,
        retry_policy="off", network_enabled=False, evidence_classification="exploratory",
        corpus_hash=corpus_hash(corpus),
        dataset_revisions={"internal": "engineering_v1"}, corpus=corpus_file or str(corpus),
    )
