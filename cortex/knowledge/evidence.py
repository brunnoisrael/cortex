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


def evidence_id(entity_id: str, kind: EvidenceType, location: str) -> str:
    raw = f"{entity_id}|{kind.value}|{location}".encode()
    return "ev-" + hashlib.sha256(raw).hexdigest()[:16]


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
    for location in entity.provenance.source_files or entity.scope:
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
                manifest = "\n".join(str(p.relative_to(root)) for p in files)
                content = manifest.encode("utf-8")
                text = "\n".join(p.read_text(encoding="utf-8", errors="ignore")[:20000] for p in files)
            else:
                content = path.read_bytes()
                text = content.decode("utf-8", errors="ignore")
            found = next((token for token in tokens if token in text or token.lower() in text.lower()), None)
            line_start = text.lower().find(found.lower()) if found else -1
            line_no = text[:line_start].count("\n") + 1 if line_start >= 0 else None
            results.append(Evidence(
                id=evidence_id(entity.id, EvidenceType.SYMBOL if found else EvidenceType.FILE, location),
                type=EvidenceType.SYMBOL if found else EvidenceType.FILE,
                location=location, fingerprint=fingerprint_bytes(content),
                observed_at=_utcnow(), status=EvidenceStatus.RESOLVED if found else EvidenceStatus.UNVERIFIABLE,
                verification_method="repository_text", line_start=line_no,
                line_end=line_no, content_excerpt=(found or text[:180]).strip(),
            ))
        except OSError:
            results.append(Evidence(
                id=evidence_id(entity.id, EvidenceType.FILE, location),
                type=EvidenceType.FILE, location=location, observed_at=_utcnow(),
                status=EvidenceStatus.UNVERIFIABLE, verification_method="filesystem",
            ))
    for commit in entity.provenance.source_commits:
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
    return results


def refresh_entity_evidence(store: KnowledgeStore, root: Path, entity: Entity) -> dict[str, Any]:
    evidence = resolve_entity_evidence(store, root, entity)
    entity.evidence = evidence
    store.upsert(entity)
    resolved = [e for e in evidence if e.status == EvidenceStatus.RESOLVED and e.fingerprint]
    return {
        "entity_id": entity.id,
        "resolved": len(resolved),
        "unverifiable": len(evidence) - len(resolved),
        "evidence": [e.model_dump(mode="json") for e in evidence],
    }


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
        "relations": store.edges_of(src=entity_id) + store.edges_of(rel="SUPERSEDES"),
    }
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(package, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return package
