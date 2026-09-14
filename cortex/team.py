"""Local-first team memory primitives (Plano de Diferenciação, Fase 9).

Sharing is opt-in and additive. A shared entity does not become ACTIVE and a
merge never overwrites either source. This module is intentionally transport
agnostic: Git, a service or a user-selected sync tool can carry the signed-ish
JSON bundle later without changing the governance rules.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from cortex.knowledge.models import Entity, Status, _utcnow
from cortex.storage.store import KnowledgeStore


class TeamError(ValueError):
    """A collaboration operation violated its explicit policy."""


class TeamRole(StrEnum):
    OWNER = "owner"
    MEMBER = "member"
    REVIEWER = "reviewer"


class Permission(StrEnum):
    READ = "read"
    PROPOSE = "propose"
    MERGE = "merge"
    ADMIN = "admin"


class TeamBundle(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    schema_: str = Field("cortex_team_bundle/v1", alias="schema")
    project: str
    exported_by: str
    exported_at: str = Field(default_factory=_utcnow)
    entities: list[dict[str, Any]]
    acl: list[dict[str, Any]]
    checksums: dict[str, str]


def _require_member(store: KnowledgeStore, project: str, principal: str,
                    minimum: TeamRole | None = None) -> dict[str, Any]:
    row = store.conn.execute(
        "SELECT * FROM team_members WHERE project = ? AND principal = ? AND revoked_at IS NULL",
        (project, principal),
    ).fetchone()
    if not row:
        raise TeamError(f"principal {principal!r} não é membro ativo de {project!r}")
    if minimum and row["role"] != minimum.value and row["role"] != TeamRole.OWNER.value:
        raise TeamError(f"operação exige papel {minimum.value}")
    return dict(row)


def add_member(store: KnowledgeStore, project: str, principal: str,
               role: TeamRole = TeamRole.MEMBER, *, actor: str) -> dict[str, Any]:
    _require_member(store, project, actor, TeamRole.OWNER) if principal != actor else None
    now = _utcnow()
    store.conn.execute(
        "INSERT INTO team_members(project, principal, role, created_at, revoked_at) VALUES (?, ?, ?, ?, NULL) "
        "ON CONFLICT(project, principal) DO UPDATE SET role=excluded.role, revoked_at=NULL",
        (project, principal, role.value, now),
    )
    store.conn.commit()
    return {"project": project, "principal": principal, "role": role.value, "created_at": now}


def revoke_member(store: KnowledgeStore, project: str, principal: str, *, actor: str) -> None:
    _require_member(store, project, actor, TeamRole.OWNER)
    store.conn.execute(
        "UPDATE team_members SET revoked_at = ? WHERE project = ? AND principal = ? AND revoked_at IS NULL",
        (_utcnow(), project, principal),
    )
    store.conn.commit()


def share_entity(store: KnowledgeStore, entity_id: str, project: str, principal: str,
                 *, actor: str, permission: Permission = Permission.READ,
                 branch: str | None = None) -> dict[str, Any]:
    _require_member(store, project, actor)
    if not store.get(entity_id):
        raise TeamError(f"entidade {entity_id!r} não encontrada")
    now = _utcnow()
    store.conn.execute(
        "INSERT INTO team_acl(entity_id, project, principal, permission, branch, granted_by, created_at, revoked_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, NULL) ON CONFLICT(entity_id, project, principal, permission, branch) "
        "DO UPDATE SET revoked_at=NULL, granted_by=excluded.granted_by",
        (entity_id, project, principal, permission.value, branch, actor, now),
    )
    store.conn.commit()
    return {"entity_id": entity_id, "project": project, "principal": principal,
            "permission": permission.value, "branch": branch, "granted_by": actor}


def visible_entities(store: KnowledgeStore, project: str, principal: str,
                     *, branch: str | None = None) -> list[Entity]:
    _require_member(store, project, principal)
    rows = store.conn.execute(
        "SELECT DISTINCT entity_id FROM team_acl WHERE project=? AND principal=? "
        "AND permission IN ('read','propose','merge','admin') AND revoked_at IS NULL "
        "AND (branch IS NULL OR branch = ?)", (project, principal, branch),
    ).fetchall()
    return [entity for row in rows if (entity := store.get(row["entity_id"])) is not None]


def merge_entities(store: KnowledgeStore, source_id: str, target_id: str, project: str,
                   *, actor: str, reason: str) -> dict[str, Any]:
    _require_member(store, project, actor, TeamRole.REVIEWER)
    if not reason.strip():
        raise TeamError("merge exige uma razão não vazia")
    source, target = store.get(source_id), store.get(target_id)
    if not source or not target:
        raise TeamError("source e target precisam existir")
    key = f"merge:{project}:{source_id}:{target_id}"
    existing = store.conn.execute("SELECT payload FROM team_receipts WHERE idempotency_key=?", (key,)).fetchone()
    if existing:
        return json.loads(existing["payload"])
    store.add_edge(target_id, "VARIANT_OF", source_id)
    payload = {"source_id": source_id, "target_id": target_id, "project": project,
               "actor": actor, "reason": reason, "history_preserved": True}
    store.conn.execute(
        "INSERT INTO team_receipts(id, action, entity_id, project, actor, payload, created_at, idempotency_key) "
        "VALUES (?, 'merge', ?, ?, ?, ?, ?, ?)",
        (f"team-{uuid.uuid4().hex[:12]}", target_id, project, actor, json.dumps(payload, sort_keys=True), _utcnow(), key),
    )
    store.conn.commit()
    return payload


def export_team_bundle(store: KnowledgeStore, project: str, principal: str, *, branch: str | None = None) -> TeamBundle:
    entities = [e.model_dump(mode="json") for e in visible_entities(store, project, principal, branch=branch)]
    acl_rows = store.conn.execute(
        "SELECT * FROM team_acl WHERE project=? AND revoked_at IS NULL ORDER BY entity_id, principal",
        (project,),
    ).fetchall()
    acl = [dict(row) for row in acl_rows]
    payload = json.dumps({"entities": entities, "acl": acl}, sort_keys=True, ensure_ascii=False).encode()
    return TeamBundle(project=project, exported_by=principal, entities=entities, acl=acl,
                      checksums={"payload": "sha256:" + hashlib.sha256(payload).hexdigest()})


def import_team_bundle(store: KnowledgeStore, bundle: TeamBundle | dict[str, Any], *, actor: str) -> dict[str, Any]:
    data = bundle if isinstance(bundle, TeamBundle) else TeamBundle.model_validate(bundle)
    _require_member(store, data.project, actor)
    payload = json.dumps({"entities": data.entities, "acl": data.acl}, sort_keys=True, ensure_ascii=False).encode()
    expected = "sha256:" + hashlib.sha256(payload).hexdigest()
    if data.checksums.get("payload") != expected:
        raise TeamError("checksum do bundle não confere")
    imported = 0
    for raw in data.entities:
        entity = Entity.model_validate(raw)
        existing = store.get(entity.id)
        if existing is None:
            entity.status = Status.PROPOSED
            store.upsert(entity)
            imported += 1
    return {"project": data.project, "imported": imported, "existing": len(data.entities) - imported,
            "authority": "proposed_until_local_review"}


def set_retention(store: KnowledgeStore, project: str, retention_days: int, *, actor: str,
                  delete_private: bool = False) -> dict[str, Any]:
    _require_member(store, project, actor, TeamRole.OWNER)
    if retention_days < 0:
        raise TeamError("retention_days não pode ser negativo")
    now = _utcnow()
    store.conn.execute(
        "INSERT INTO team_retention(project, retention_days, delete_private, updated_at, updated_by) VALUES(?,?,?,?,?) "
        "ON CONFLICT(project) DO UPDATE SET retention_days=excluded.retention_days, "
        "delete_private=excluded.delete_private, updated_at=excluded.updated_at, updated_by=excluded.updated_by",
        (project, retention_days, int(delete_private), now, actor),
    )
    store.conn.commit()
    return {"project": project, "retention_days": retention_days, "delete_private": delete_private}


def apply_retention(store: KnowledgeStore, project: str, *, actor: str, now: datetime | None = None) -> dict[str, Any]:
    _require_member(store, project, actor, TeamRole.OWNER)
    policy = store.conn.execute("SELECT * FROM team_retention WHERE project=?", (project,)).fetchone()
    if not policy:
        raise TeamError(f"nenhuma política de retenção para {project!r}")
    cutoff = (now or datetime.now(UTC)) - timedelta(days=policy["retention_days"])
    rows = store.conn.execute(
        "SELECT DISTINCT entity_id FROM team_acl WHERE project=? AND revoked_at IS NOT NULL AND revoked_at < ?",
        (project, cutoff.strftime("%Y-%m-%dT%H:%M:%SZ")),
    ).fetchall()
    # Team metadata is safe to purge; entities remain recoverable in the local ledger.
    for row in rows:
        store.conn.execute("DELETE FROM team_acl WHERE project=? AND entity_id=? AND revoked_at IS NOT NULL",
                           (project, row["entity_id"]))
    store.conn.commit()
    return {"project": project, "purged_acl": len(rows), "entities_deleted": 0,
            "reason": "ledger_preserved"}
