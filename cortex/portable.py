"""Portable, versioned exports and derived instruction files.

SQLite remains the local index, while this module provides a stable JSON/Git
surface for audit, migration and repositories that prefer reviewed Markdown.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from cortex.knowledge.models import ArtifactType, Authority, Entity, Provenance, Status
from cortex.storage.store import KnowledgeStore

EXPORT_SCHEMA = "cortex_export/v1"
MARKDOWN_SCHEMA = "cortex_markdown/v1"


def export_store(store: KnowledgeStore, output: Path | None = None, *, include_events: bool = True) -> dict[str, Any]:
    entities = sorted(store.all_entities(), key=lambda item: item.id)
    package: dict[str, Any] = {
        "cortex_schema": EXPORT_SCHEMA,
        "schema_version": 1,
        "entities": [entity.model_dump(mode="json") for entity in entities],
        "edges": sorted(store.edges_of(), key=lambda edge: (edge["src"], edge["rel"], edge["dst"])),
        "governance_receipts": sorted(store.governance_receipts(), key=lambda row: row["id"]),
        "sessions": [dict(row) for row in store.conn.execute("SELECT * FROM sessions ORDER BY id").fetchall()],
    }
    if include_events:
        package["events"] = store.all_events()
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(package, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return package


def _validate_package(package: dict[str, Any]) -> None:
    if package.get("cortex_schema") != EXPORT_SCHEMA:
        raise ValueError(f"unsupported export schema: {package.get('cortex_schema')!r}")
    if package.get("schema_version") != 1:
        raise ValueError("unsupported export schema version")


def import_store(
    store: KnowledgeStore,
    package: dict[str, Any],
    *,
    actor: str = "import",
    trusted: bool = False,
) -> dict[str, Any]:
    """Import a package without activating external knowledge by default."""
    _validate_package(package)
    imported: list[str] = []
    remap: dict[str, str] = {}
    pending: list[tuple[str, Entity]] = []
    for raw in package.get("entities", []):
        entity = Entity.model_validate(raw)
        original_id = entity.id
        if store.get(entity.id):
            entity.id = store.reserve_entity_id(entity.type)
            remap[original_id] = entity.id
        if not trusted and entity.status in {
            Status.ACTIVE, Status.VALIDATED, Status.IMPLEMENTED,
        }:
            entity.status = Status.PROPOSED
            entity.authority = Authority.AGENT_INFERRED
            entity.details = {**entity.details, "imported_requires_review": True, "imported_by": actor}
        pending.append((original_id, entity))
        imported.append(entity.id)
    if trusted:
        for receipt in package.get("governance_receipts", []):
            entity_id = remap.get(receipt["entity_id"], receipt["entity_id"])
            if not any(entity.id == entity_id for _, entity in pending):
                continue
            store.conn.execute(
                "INSERT OR IGNORE INTO governance_receipts "
                "(id, entity_id, action, from_status, to_status, actor, reason, evidence_ids, created_at, idempotency_key) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (f"gvr-import-{uuid.uuid4().hex[:12]}", entity_id, receipt["action"],
                 receipt.get("from_status"), receipt["to_status"], receipt.get("actor", actor),
                 receipt.get("reason", "imported"), receipt.get("evidence_ids", "[]"),
                 receipt.get("created_at") or "", f"import:{uuid.uuid4().hex}"),
            )
        store.conn.commit()
    for _original_id, entity in pending:
        store.upsert(entity)
    for edge in package.get("edges", []):
        src, dst = remap.get(edge["src"], edge["src"]), remap.get(edge["dst"], edge["dst"])
        if src in imported or dst in imported:
            store.add_edge(src, edge["rel"], dst)
    for session in package.get("sessions", []):
        if session.get("id"):
            store.ensure_session(
                session["id"], session.get("host") or "import",
                branch=session.get("branch"), agent=session.get("agent"), phase=session.get("phase"),
            )
    for event in package.get("events", []):
        store.add_event(event)
    return {"schema": EXPORT_SCHEMA, "imported": imported, "remapped": remap, "trusted": trusted}


def export_markdown(store: KnowledgeStore, output: Path | None = None) -> str:
    """Render active knowledge as a reviewed, source-linked Markdown view."""
    lines = [
        "<!-- CORTEX DERIVED KNOWLEDGE: generated output; SQLite/JSON ledger is the source of truth. -->",
        f"<!-- schema: {MARKDOWN_SCHEMA} -->",
        "# Cortex engineering knowledge",
        "",
    ]
    for entity in sorted(store.all_entities(), key=lambda item: (item.type.value, item.id)):
        if not entity.is_current or entity.status != Status.ACTIVE:
            continue
        lines.append(f"## [{entity.id}] {entity.type.value}")
        lines.append("")
        lines.append(entity.statement)
        refs = [item.location for item in entity.evidence if item.status.value == "resolved"]
        if refs:
            lines.append("")
            lines.append("Evidence: " + ", ".join(sorted(set(refs))))
        lines.append("")
    content = "\n".join(lines).rstrip() + "\n"
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
    return content


def import_markdown(store: KnowledgeStore, source: str | Path, *, actor: str = "markdown_import") -> dict[str, Any]:
    """Import the stable derived format as proposed knowledge."""
    text = Path(source).read_text(encoding="utf-8") if isinstance(source, Path) else source
    if "cortex_markdown/v1" not in text:
        raise ValueError("unsupported Cortex Markdown schema")
    imported: list[str] = []
    current: dict[str, str] | None = None
    for line in text.splitlines():
        if line.startswith("## [") and "] " in line:
            header, kind = line[4:].split("] ", 1)
            current = {"id": header, "kind": kind}
        elif current and line.strip() and not line.startswith("Evidence:"):
            etype = current["kind"] if current["kind"] in {item.value for item in ArtifactType} else "idea"
            entity = Entity(
                id=store.reserve_entity_id(ArtifactType(etype)), type=ArtifactType(etype),
                statement=line.strip(), status=Status.PROPOSED,
                authority=Authority.AGENT_INFERRED,
                details={"imported_from": current["id"], "imported_by": actor, "imported_requires_review": True},
                provenance=Provenance(extraction_source="markdown_import"),
            )
            store.upsert(entity)
            imported.append(entity.id)
            current = None
    return {"schema": MARKDOWN_SCHEMA, "imported": imported}


def render_derived_rules(store: KnowledgeStore, target: Path | None = None) -> str:
    """Create AGENTS/CLAUDE/Cursor-compatible output, never a source of truth."""
    lines = [
        "# Derived Cortex rules",
        "",
        "> Generated by Cortex. Do not edit as the source of truth; update the ledger and regenerate.",
        "",
    ]
    for entity in sorted(store.all_entities(), key=lambda item: item.id):
        if entity.status != Status.ACTIVE or entity.type.value not in {"adr", "correnda", "negative_knowledge"}:
            continue
        lines.append(f"- [{entity.id}] {entity.statement}")
    content = "\n".join(lines).rstrip() + "\n"
    if target is not None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return content
