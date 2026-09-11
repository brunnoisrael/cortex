"""Review/impact integration for commits, diffs and pull-request references."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cortex.knowledge.models import ArtifactType, Authority, Entity, Provenance, Status, _utcnow
from cortex.storage.store import KnowledgeStore
from cortex.verification import changed_paths


def _overlaps(entity: Entity, paths: list[str]) -> bool:
    if not entity.scope:
        return bool(paths)
    return any(path.startswith(scope.replace("\\", "/")) or scope.replace("\\", "/") in path
               for path in paths for scope in entity.scope)


def build_review_summary(
    store: KnowledgeStore,
    root: Path,
    *,
    base: str = "HEAD",
    commit: str | None = None,
    pull_request: str | None = None,
    paths: list[str] | None = None,
) -> Entity:
    """Create a review artifact linking impacted knowledge and missing proof."""
    changed = list(dict.fromkeys(paths or changed_paths(root, base)))
    source = pull_request or commit or base
    impacted = [entity for entity in store.all_entities() if entity.is_current and _overlaps(entity, changed)]
    conflicts = [case for case in store.contradiction_cases()
                 if case["src"] in {entity.id for entity in impacted}
                 or case["dst"] in {entity.id for entity in impacted}]
    missing = [entity.id for entity in impacted if not any(
        evidence.status.value == "resolved" for evidence in entity.evidence
    )]
    review_id = store.reserve_entity_id(ArtifactType.REVIEW)
    review = Entity(
        id=review_id, type=ArtifactType.REVIEW,
        statement=f"Engineering review impact: {source}",
        status=Status.PROPOSED, authority=Authority.OBSERVED, confidence=0.9,
        scope=changed, observed_at=_utcnow(),
        details={
            "source_kind": "pull_request" if pull_request else "commit" if commit else "diff",
            "source": source, "base": base, "changed_paths": changed,
            "impacted_entities": [entity.id for entity in impacted],
            "decisions_impacted": [entity.id for entity in impacted if entity.type == ArtifactType.ADR],
            "rules_applicable": [entity.id for entity in impacted if entity.type == ArtifactType.CORRENDA],
            "negative_knowledge": [entity.id for entity in impacted if entity.type == ArtifactType.NEGATIVE_KNOWLEDGE],
            "conflicts": conflicts, "missing_evidence": missing,
        },
        provenance=Provenance(source_files=changed, extraction_source="engineering_review"),
    )
    store.upsert(review)
    for entity in impacted:
        store.add_edge(review.id, "AFFECTS", entity.id)
    if commit:
        store.add_edge(review.id, "EVIDENCED_BY", commit)
    return review


def review_as_dict(store: KnowledgeStore, review_id: str) -> dict[str, Any]:
    review = store.get(review_id)
    if not review or review.type != ArtifactType.REVIEW:
        raise ValueError(f"review {review_id} not found")
    return {
        "id": review.id,
        "statement": review.statement,
        "status": review.status.value,
        "details": review.details,
        "affected": [entity.id for _rel, entity in store.related(review.id, rel="AFFECTS")],
        "receipts": store.governance_receipts(review.id),
    }


def render_review_markdown(summary: dict[str, Any]) -> str:
    details = summary["details"]
    lines = [f"# {summary['statement']}", "", f"- Review: `{summary['id']}`", f"- Status: `{summary['status']}`", ""]
    for title, key in (
        ("Decisions impacted", "decisions_impacted"),
        ("Applicable rules", "rules_applicable"),
        ("Negative knowledge", "negative_knowledge"),
        ("Missing evidence", "missing_evidence"),
    ):
        lines.append(f"## {title}")
        values = details.get(key) or []
        lines.extend(f"- `{value}`" for value in values) if values else lines.append("- none")
        lines.append("")
    lines.append("## Conflicts")
    conflicts = details.get("conflicts") or []
    if conflicts:
        lines.extend(f"- `{item['src']}` contradicts `{item['dst']}` ({item['type']})" for item in conflicts)
    else:
        lines.append("- none")
    return "\n".join(lines).rstrip() + "\n"


def review_as_json(store: KnowledgeStore, review_id: str) -> str:
    return json.dumps(review_as_dict(store, review_id), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
