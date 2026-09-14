import pytest

from cortex.knowledge.models import ArtifactType, Entity, Status
from cortex.team import (
    Permission,
    TeamError,
    TeamRole,
    add_member,
    apply_retention,
    export_team_bundle,
    import_team_bundle,
    merge_entities,
    set_retention,
    share_entity,
    visible_entities,
)


def _entity(store, entity_id: str) -> None:
    store.upsert(Entity(id=entity_id, type=ArtifactType.ADR, statement=entity_id,
                        status=Status.PROPOSED, scope=["src"]))


def test_team_sharing_is_opt_in_and_branch_scoped(store):
    _entity(store, "adr-team-1")
    add_member(store, "cortex", "alice", TeamRole.OWNER, actor="alice")
    add_member(store, "cortex", "bob", actor="alice")
    share_entity(store, "adr-team-1", "cortex", "bob", actor="alice", branch="main")
    assert [e.id for e in visible_entities(store, "cortex", "bob", branch="main")] == ["adr-team-1"]
    assert visible_entities(store, "cortex", "bob", branch="feature") == []


def test_merge_is_non_destructive_idempotent_and_audited(store):
    _entity(store, "adr-old")
    _entity(store, "adr-new")
    add_member(store, "cortex", "owner", TeamRole.OWNER, actor="owner")
    first = merge_entities(store, "adr-old", "adr-new", "cortex", actor="owner", reason="decisão revisada")
    second = merge_entities(store, "adr-old", "adr-new", "cortex", actor="owner", reason="não deve duplicar")
    assert first == second
    assert store.get("adr-old").status == Status.PROPOSED
    assert store.edges_of(src="adr-new", rel="VARIANT_OF")
    assert len(store.conn.execute("SELECT * FROM team_receipts").fetchall()) == 1


def test_bundle_checksum_and_external_knowledge_stays_proposed(store, tmp_path):
    _entity(store, "adr-bundle")
    add_member(store, "cortex", "alice", TeamRole.OWNER, actor="alice")
    share_entity(store, "adr-bundle", "cortex", "alice", actor="alice", permission=Permission.READ)
    bundle = export_team_bundle(store, "cortex", "alice")
    bundle.entities[0]["status"] = "active"
    with pytest.raises(TeamError, match="checksum"):
        import_team_bundle(store, bundle, actor="alice")
    bundle = export_team_bundle(store, "cortex", "alice")
    clean = type(store)(tmp_path / "clean.db")
    try:
        result = import_team_bundle(clean, bundle, actor="alice")
    except TeamError:
        add_member(clean, "cortex", "alice", TeamRole.OWNER, actor="alice")
        result = import_team_bundle(clean, bundle, actor="alice")
    assert result["imported"] == 1
    assert clean.get("adr-bundle").status == Status.PROPOSED
    clean.close()


def test_retention_purges_revoked_acl_but_never_entities(store):
    _entity(store, "adr-retain")
    add_member(store, "cortex", "owner", TeamRole.OWNER, actor="owner")
    share_entity(store, "adr-retain", "cortex", "owner", actor="owner")
    store.conn.execute("UPDATE team_acl SET revoked_at='2020-01-01T00:00:00Z'")
    store.conn.commit()
    set_retention(store, "cortex", 30, actor="owner")
    result = apply_retention(store, "cortex", actor="owner")
    assert result["purged_acl"] == 1
    assert result["entities_deleted"] == 0
    assert store.get("adr-retain") is not None
