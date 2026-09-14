"""Reproducibility manifest and deterministic environment metadata."""

from __future__ import annotations

import hashlib
import json
import platform
import random
import sys
from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from .schema import _BenchmarkModel

PRIMARY_ENDPOINTS = {
    "exact_recall": ("recall_at_k", "evidence_resolution_rate"),
    "aggregation": ("set_f1", "scope_accuracy"),
    "tracking": ("current_state_accuracy", "supersession_accuracy"),
    "deletion": ("deletion_compliance", "stale_leak_rate"),
    "cascade": ("cascade_correctness_hop1", "lineage_completeness"),
    "absence": ("abstention_recall", "false_certainty_rate"),
}


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
    seed: int
    retry_policy: Literal["deterministic", "off"] = "off"
    network_enabled: Literal[False] = False
    corpus_hash: str
    dataset_revisions: dict[str, str] = Field(default_factory=dict)
    corpus: str | None = None
    cases: list[dict[str, Any]] | None = None


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
        retry_policy="off", network_enabled=False, corpus_hash=corpus_hash(corpus),
        dataset_revisions={"internal": "engineering_v1"}, corpus=corpus_file or str(corpus),
    )
