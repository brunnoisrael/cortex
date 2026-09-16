"""Evidence Ledger: reproducible support for engineering knowledge.

The ledger deliberately keeps a citation (source/provenance) distinct from a
proof.  A source can be unavailable or change; an Evidence record says what
was actually resolved, fingerprinted and checked at a point in time.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from cortex.knowledge.models import (
    Entity,
    Evidence,
    EvidenceStatus,
    EvidenceType,
    _utcnow,
)
from cortex.storage.store import KnowledgeStore


def fingerprint_bytes(content: bytes) -> str:
    return "sha256:" + hashlib.sha256(content).hexdigest()


def fingerprint_text(content: str) -> str:
    return fingerprint_bytes(content.encode("utf-8"))


def fingerprint_directory(root: Path, directory: Path) -> str:
    """Fingerprint a bounded directory manifest for read-only diff checks."""
    files = sorted(path for path in directory.rglob("*") if path.is_file())[:200]
    manifest = "\n".join(
        f"{path.relative_to(root)}|{fingerprint_bytes(path.read_bytes())}" for path in files
    )
    return fingerprint_text(manifest)


def fingerprint_event(event: dict[str, Any] | None) -> str | None:
    if not event:
        return None
    payload = f"{event.get('id')}|{event.get('type')}|{event.get('content') or ''}"
    return fingerprint_text(payload)


def evidence_id(
    entity_id: str,
    kind: EvidenceType,
    location: str | None = None,
    extra: str | None = None,
) -> str:
    loc = str(location).strip() if location else "none"
    raw = f"{entity_id}|{kind.value}|{loc}"
    if extra:
        raw += f"|{str(extra).strip()}"
    return "ev-" + hashlib.sha256(raw.encode()).hexdigest()[:16]


def _safe_path(root: Path, location: str) -> Path | None:
    candidate = (root / location).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate


def resolve_entity_evidence(store: KnowledgeStore, root: Path, entity: Entity) -> list[Evidence]:
    """Resolve file, symbol and commit citations without promoting authority."""
    results: list[Evidence] = []
    tokens = [
        token for value in [entity.statement, *entity.details.values()]
        if isinstance(value, str)
        for token in value.replace("(", " ").replace(")", " ").split()
        if len(token) > 2 and token.replace("_", "").isalnum()
    ][:8]
    cited_files = list(dict.fromkeys(
        [str(f).strip() for f in entity.provenance.source_files if f and str(f).strip()]
        + [str(item).strip() for item in entity.details.get("affected_files", []) if isinstance(item, str) and item.strip()]
        + [str(item).strip() for item in entity.scope if isinstance(item, str) and item.strip()]
    ))
    line_refs = entity.details.get("line_refs") or {}
    for location in cited_files:
        path = _safe_path(root, location)
        if path is None or not path.exists():
            results.append(Evidence(
                id=evidence_id(entity.id, EvidenceType.FILE, location),
                type=EvidenceType.FILE, location=location, observed_at=_utcnow(),
                status=EvidenceStatus.UNVERIFIABLE,
                verification_method="filesystem",
            ))
            continue
        try:
            if path.is_dir():
                files = sorted(p for p in path.rglob("*") if p.is_file())[:200]
                manifest = "\n".join(
                    f"{p.relative_to(root)}|{fingerprint_bytes(p.read_bytes())}" for p in files
                )
                content = manifest.encode("utf-8")
                text = "\n".join(p.read_text(encoding="utf-8", errors="ignore")[:20000] for p in files)
            else:
                content = path.read_bytes()
                text = content.decode("utf-8", errors="ignore")
            found = next((token for token in tokens if token in text or token.lower() in text.lower()), None)
            line_start = text.lower().find(found.lower()) if found else -1
            line_no = text[:line_start].count("\n") + 1 if line_start >= 0 else None
            file_fingerprint = fingerprint_bytes(content)
            results.append(Evidence(
                id=evidence_id(entity.id, EvidenceType.FILE, location),
                type=EvidenceType.FILE, location=location, fingerprint=file_fingerprint,
                observed_at=_utcnow(), status=EvidenceStatus.RESOLVED,
                verification_method="filesystem_fingerprint",
                content_excerpt=text[:180].strip(),
            ))
            if tokens:
                results.append(Evidence(
                    id=evidence_id(entity.id, EvidenceType.SYMBOL, location),
                    type=EvidenceType.SYMBOL, location=location, fingerprint=file_fingerprint,
                    observed_at=_utcnow(), status=EvidenceStatus.RESOLVED if found else EvidenceStatus.UNVERIFIABLE,
                    verification_method="repository_text", line_start=line_no,
                    line_end=line_no, content_excerpt=(found or "").strip(),
                ))
            if location in line_refs:
                requested_line = line_refs[location]
                results.append(Evidence(
                    id=evidence_id(entity.id, EvidenceType.LINE, f"{location}:{requested_line}"),
                    type=EvidenceType.LINE, location=f"{location}:{requested_line}",
                    fingerprint=file_fingerprint, observed_at=_utcnow(),
                    status=EvidenceStatus.RESOLVED if line_no is not None else EvidenceStatus.UNVERIFIABLE,
                    verification_method="line_reference", line_start=int(requested_line),
                    line_end=int(requested_line),
                ))
        except OSError:
            results.append(Evidence(
                id=evidence_id(entity.id, EvidenceType.FILE, location),
                type=EvidenceType.FILE, location=location, observed_at=_utcnow(),
                status=EvidenceStatus.UNVERIFIABLE, verification_method="filesystem",
            ))
    source_events = list(dict.fromkeys(
        [str(e).strip() for e in entity.provenance.source_events if e and str(e).strip()]
    ))
    for event_id in source_events:
        event = next((item for item in store.all_events() if item["id"] == event_id), None)
        results.append(Evidence(
            id=evidence_id(entity.id, EvidenceType.EVENT, event_id),
            type=EvidenceType.EVENT, location=event_id,
            fingerprint=fingerprint_event(event),
            observed_at=(event or {}).get("ts") or _utcnow(),
            status=EvidenceStatus.RESOLVED if event else EvidenceStatus.UNVERIFIABLE,
            verification_method="event_store",
        ))
    source_commits = list(dict.fromkeys(
        [str(c).strip() for c in entity.provenance.source_commits if c and str(c).strip()]
    ))
    for commit in source_commits:
        resolved = False
        try:
            subprocess.run(
                ["git", "-C", str(root), "cat-file", "-e", f"{commit}^{{commit}}"],
                capture_output=True, timeout=5, check=True,
            )
            resolved = True
        except Exception:
            pass
        results.append(Evidence(
            id=evidence_id(entity.id, EvidenceType.COMMIT, commit),
            type=EvidenceType.COMMIT, location=commit,
            fingerprint="git:" + commit if resolved else None,
            observed_at=_utcnow(), status=EvidenceStatus.RESOLVED if resolved else EvidenceStatus.UNVERIFIABLE,
            verification_method="git_cat_file",
            commit=commit,
        ))
    test_locations = list(dict.fromkeys(
        [str(item).strip() for item in (entity.details.get("tests", []) or entity.details.get("test_files", []) or [])
         if isinstance(item, str) and item.strip()]
    ))
    for test_location in test_locations:
        path = _safe_path(root, test_location)
        exists = path is not None and path.is_file()
        fingerprint = fingerprint_bytes(path.read_bytes()) if exists and path is not None else None
        results.append(Evidence(
            id=evidence_id(entity.id, EvidenceType.TEST, test_location),
            type=EvidenceType.TEST, location=test_location, fingerprint=fingerprint,
            observed_at=_utcnow(), status=EvidenceStatus.RESOLVED if exists else EvidenceStatus.UNVERIFIABLE,
            verification_method="test_file", content_excerpt="test file exists" if exists else None,
        ))
    review_ids = entity.details.get("review_ids", []) or []
    if entity.details.get("review_id"):
        review_ids = [*review_ids, entity.details["review_id"]]
    for review_id in dict.fromkeys(str(item).strip() for item in review_ids if item and str(item).strip()):
        review = store.get(review_id)
        resolved = review is not None and review.type.value == "review"
        fingerprint = fingerprint_text(review.statement) if resolved and review is not None else None
        results.append(Evidence(
            id=evidence_id(entity.id, EvidenceType.REVIEW, review_id),
            type=EvidenceType.REVIEW, location=review_id, fingerprint=fingerprint,
            observed_at=_utcnow(), status=EvidenceStatus.RESOLVED if resolved else EvidenceStatus.UNVERIFIABLE,
            verification_method="cortex_review",
        ))
    # Guarantee no duplicate evidence IDs within the returned list
    seen_ids: set[str] = set()
    deduped: list[Evidence] = []
    for item in results:
        if item.id not in seen_ids:
            seen_ids.add(item.id)
            deduped.append(item)
    return deduped


def refresh_entity_evidence(store: KnowledgeStore, root: Path, entity: Entity) -> dict[str, Any]:
    previous = {item.id: item for item in store.list_evidence(entity.id)}
    evidence = resolve_entity_evidence(store, root, entity)
    changed = []
    for item in evidence:
        old = previous.get(item.id)
        if old and old.fingerprint and item.fingerprint and old.fingerprint != item.fingerprint:
            item.status = EvidenceStatus.STALE
            changed.append(item.id)
    entity.evidence = evidence
    if changed:
        entity.freshness.stale = True
    store.upsert(entity)
    resolved = [e for e in evidence if e.status == EvidenceStatus.RESOLVED and e.fingerprint]
    required = [e for e in evidence if e.type in {
        EvidenceType.FILE, EvidenceType.SYMBOL, EvidenceType.LINE, EvidenceType.COMMIT,
        EvidenceType.TEST, EvidenceType.REVIEW,
    }]
    resolved_required = [e for e in resolved if e.type in {
        EvidenceType.FILE, EvidenceType.SYMBOL, EvidenceType.LINE, EvidenceType.COMMIT,
        EvidenceType.TEST, EvidenceType.REVIEW,
    }]
    return {
        "entity_id": entity.id,
        "resolved": len(resolved),
        "unverifiable": len(evidence) - len(resolved),
        "required": len(required),
        "strictly_verified": bool(required) and len(resolved_required) == len(required) and not changed,
        "changed": changed,
        "evidence": [e.model_dump(mode="json") for e in evidence],
    }


def record_test_result(
    store: KnowledgeStore,
    entity_id: str,
    test_name: str,
    *,
    passed: bool,
    output: str = "",
    commit: str | None = None,
) -> Evidence:
    """Attach a test result as evidence without claiming it proves the ADR."""
    entity = store.get(entity_id)
    if entity is None:
        raise ValueError(f"entity {entity_id} not found")
    payload = f"{test_name}|{passed}|{output}"
    evidence = Evidence(
        id=evidence_id(entity_id, EvidenceType.TEST, test_name),
        type=EvidenceType.TEST, location=test_name,
        fingerprint=fingerprint_text(payload), observed_at=_utcnow(),
        status=EvidenceStatus.RESOLVED if passed else EvidenceStatus.STALE,
        verification_method="test_runner", content_excerpt=output[-500:], commit=commit,
    )
    entity.evidence = [item for item in entity.evidence if item.id != evidence.id] + [evidence]
    store.upsert(entity)
    return evidence


def export_evidence_package(store: KnowledgeStore, entity_id: str, output: Path | None = None) -> dict[str, Any]:
    """Export a deterministic, self-contained audit package as JSON."""
    entity = store.get(entity_id)
    if entity is None:
        raise ValueError(f"entity {entity_id} not found")
    package = {
        "cortex_schema": "evidence_ledger/v1",
        "entity": entity.model_dump(mode="json"),
        "evidence": [e.model_dump(mode="json") for e in store.list_evidence(entity_id)],
        "receipts": store.governance_receipts(entity_id),
        "relations": [
            edge for edge in store.edges_of()
            if edge["src"] == entity_id or edge["dst"] == entity_id
        ],
    }
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(package, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return package
