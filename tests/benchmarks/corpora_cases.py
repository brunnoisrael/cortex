"""Access to the committed corpora through the same builder that generated it."""

from __future__ import annotations

from typing import Any

from cortex.benchmarks.corpora.build_internal import (
    ADVERSARIAL_CASES,
    CASES,
)
from cortex.benchmarks.corpora.build_internal import (
    build_case as build_raw_case,
)

__all__ = ["ALL_CASES", "build_case", "case_by_id"]

ALL_CASES = [*CASES, *ADVERSARIAL_CASES]


def case_by_id(case_id: str) -> dict[str, Any]:
    for case in ALL_CASES:
        if case["id"] == case_id:
            return case
    raise KeyError(f"unknown internal case: {case_id}")


def build_case(case_id: str, *, filler: str = "nofiller") -> dict[str, Any]:
    """The committed representation of one internal case, checksums included."""
    return build_raw_case(case_by_id(case_id), filler=filler)
