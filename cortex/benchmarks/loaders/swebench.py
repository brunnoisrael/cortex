from __future__ import annotations

import json
from pathlib import Path

from ..errors import LeakageError, SchemaError
from ..schema import BenchmarkInstance, Gold, instance_from_dict

# Gate of plan §Onda 2: a SWE-bench case may only enter the corpus when every
# one of these fields is present, so the cutoff, the repository identity and
# the absence of the patch in the input are provable rather than assumed.
REQUIRED_FIELDS = ("repo", "instance_id", "base_commit", "problem_statement", "patch", "test_patch")

# Kappa thresholds of plan §9.2; below them the annotation is exploratory and
# can never back a release claim.
KAPPA_BINARY_MIN = 0.6
KAPPA_ORDINAL_MIN = 0.5


def load_swebench(path: Path, *, split: str = "dev") -> list[BenchmarkInstance]:
    """Normalize local SWE-bench metadata; patch fields never enter history.

    ``patch`` and ``test_patch`` are read only to (a) satisfy the exclusion
    gate and (b) be stored as gold, which is evaluation-only data.  After
    normalization the loader re-serializes the *adapter-visible* projection and
    asserts the patch bytes are not present in it.
    """
    rows = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(rows, dict):
        rows = rows.get("data", rows.get("instances", []))
    result: list[BenchmarkInstance] = []
    for row in rows:
        _assert_gate(row)
        raw = dict(row.get("normalized", row))
        raw.pop("patch", None)
        raw.pop("test_patch", None)
        gold = dict(raw.get("gold") or {})
        gold["answer"] = row["patch"]
        gold.setdefault("gold_evidence", row.get("gold_evidence", []))
        agreement = row.get("annotation_agreement")
        gold["annotation_quality"] = _annotation_quality(agreement)
        # An exploratory annotation must still carry its measured kappa, so the
        # report can show *how far* the annotation is from the threshold.
        gold["annotation_agreement"] = agreement or {"kappa": 0.0}
        raw["gold"] = gold
        raw.setdefault("source", "swebench")
        raw.setdefault("source_revision", str(row.get("base_commit", "local")))
        raw.setdefault("split", split)
        raw.setdefault("domain", "software_project")
        raw.setdefault("metadata", {})
        raw["metadata"] = {
            **(raw["metadata"] if isinstance(raw["metadata"], dict) else {}),
            "transform": "swebench/local-json-normalized",
            "repo": row.get("repo"),
            "instance_id": row.get("instance_id"),
            "base_commit": row.get("base_commit"),
            "patch_excluded": True,
            "observed_facts": row.get("observed_facts", []),
            "inferences": row.get("inferences", []),
        }
        instance = instance_from_dict(raw)
        _assert_patch_absent(instance, row)
        result.append(instance)
    return result


def _assert_gate(row: dict) -> None:
    missing = [field for field in REQUIRED_FIELDS if field not in row or row[field] in (None, "")]
    if missing:
        raise SchemaError(f"SWE-bench row is missing {missing}; the Onda 2 gate requires cutoff, repo, "
                          "base_commit, problem statement and both patch fields to prove exclusion")


def _annotation_quality(agreement: dict | None) -> str:
    """Blind-annotation protocol: below the kappa thresholds the case is
    exploratory and is excluded from confirmatory claims (plan §9.2)."""
    if not agreement:
        return "exploratory"
    kappa = agreement.get("kappa")
    if kappa is None:
        return "exploratory"
    threshold = KAPPA_ORDINAL_MIN if agreement.get("scale") == "ordinal" else KAPPA_BINARY_MIN
    return "confirmatory" if kappa >= threshold else "exploratory"


def _assert_patch_absent(instance: BenchmarkInstance, row: dict) -> None:
    projection = instance.model_copy(
        update={"gold": Gold(answer=None, expected_abstention=False, gold_evidence=[])}
    ).model_dump_json()
    for secret in (row["patch"], row["test_patch"]):
        if secret and secret in projection:
            raise LeakageError(f"patch leaked into normalized SWE-bench instance {instance.id}")
