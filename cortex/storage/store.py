"""SQLite knowledge store with WAL and FTS5 (PRD §23).

Implements the KnowledgeStore contract:
upsert / get / search / related / history.

Migration rules (PRD: never destroy history):
- migrations are additive and idempotent, never destructive;
- each step is a callable keyed by the schema version it upgrades TO;
- legacy stores (created before versioning) are treated as version 1.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from collections.abc import Callable
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from cortex.knowledge.models import (
    ArtifactType,
    Authority,
    Entity,
    Status,
    _utcnow,
)

SCHEMA_VERSION = 2

# Maps ArtifactType -> short id prefix used by reserve_entity_id.
_PREFIX_BY_TYPE: dict[ArtifactType, str] = {
    ArtifactType.INTENTION: "int",
    ArtifactType.ADR: "adr",
    ArtifactType.FIX: "fix",
    ArtifactType.CORRENDA: "cor",
    ArtifactType.REVIEW: "rev",
    ArtifactType.NEGATIVE_KNOWLEDGE: "nk",
    ArtifactType.IDEA: "idea",
}


def _migration_002_events_host(conn: sqlite3.Connection) -> None:
    """002 (additive): events gain a `host` column for hook-adapter context.
    Legacy rows keep NULL; idempotent — skips when the column already exists."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(events)")}
    if "host" not in cols:
        conn.execute("ALTER TABLE events ADD COLUMN host TEXT")


MIGRATIONS: dict[int, Callable[[sqlite3.Connection], None]] = {
    2: _migration_002_events_host,
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    host TEXT,
    started_at TEXT,
    ended_at TEXT,
    phase TEXT,
    branch TEXT,
    agent TEXT
);
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    session_id TEXT,
    ts TEXT NOT NULL,
    content TEXT,
    files TEXT,
    branch TEXT,
    meta TEXT,
    host TEXT,
    distilled INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);
CREATE INDEX IF NOT EXISTS idx_events_distilled ON events(distilled);
CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);
CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    status TEXT NOT NULL,
    authority TEXT NOT NULL,
    confidence REAL NOT NULL,
    statement TEXT NOT NULL,
    details TEXT NOT NULL,
    scope TEXT NOT NULL,
    phase TEXT,
    session_id TEXT,
    provenance TEXT NOT NULL,
    freshness TEXT NOT NULL,
    superseded_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
CREATE INDEX IF NOT EXISTS idx_entities_status ON entities(status);
CREATE INDEX IF NOT EXISTS idx_entities_session ON entities(session_id);
CREATE INDEX IF NOT EXISTS idx_entities_created_at ON entities(created_at);
CREATE TABLE IF NOT EXISTS edges (
    src TEXT NOT NULL,
    rel TEXT NOT NULL,
    dst TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (src, rel, dst)
);
CREATE INDEX IF NOT EXISTS idx_edges_src ON edges(src);
CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges(dst);
CREATE INDEX IF NOT EXISTS idx_edges_rel ON edges(rel);
CREATE TABLE IF NOT EXISTS entity_seq (
    prefix TEXT PRIMARY KEY,
    last INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS distill_runs (
    ts TEXT NOT NULL,
    session TEXT,
    summary TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_distill_runs_ts ON distill_runs(ts);
CREATE VIRTUAL TABLE IF NOT EXISTS entities_fts USING fts5(
    id UNINDEXED, text
);
"""


class KnowledgeStore:
    MAX_SEARCH_LIMIT = 500

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # Three processes write concurrently (CLI + MCP + hook subprocess):
        # a busy timeout prevents spurious "database is locked"; autocommit
        # isolation makes the explicit BEGIN IMMEDIATE in _mint_seq safe.
        self.conn = sqlite3.connect(str(self.db_path), timeout=30.0,
                                    isolation_level=None)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA busy_timeout=30000")
        res = self.conn.execute("PRAGMA journal_mode=WAL").fetchone()
        if res is None or str(res[0]).lower() != "wal":
            logging.getLogger("cortex.store").warning(
                "WAL mode not active (%s); concurrent access may fail", res)
        self.conn.execute("PRAGMA foreign_keys=ON")
        # Count of entity rows skipped for being malformed (surfaced by doctor).
        self.malformed_rows: int = 0
        self.schema_version: int = SCHEMA_VERSION
        self.conn.executescript(SCHEMA)
        self._migrate()

    def __enter__(self) -> "KnowledgeStore":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        self.conn.close()  # idempotent in CPython sqlite3

    @contextmanager
    def _write_txn(self):
        """Explicit IMMEDIATE write transaction (autocommit connection)."""
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.conn.execute("COMMIT")
        except Exception:
            self.conn.execute("ROLLBACK")
            raise

    def _migrate(self) -> None:
        stored = self.conn.execute("PRAGMA user_version").fetchone()[0]
        version = stored
        if version == 0:
            # Fresh store (schema just created) or legacy pre-versioning store.
            has_entities = self.conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='entities'"
            ).fetchone() is not None
            version = 1 if has_entities else SCHEMA_VERSION
        for step in sorted(MIGRATIONS):
            if version < step <= SCHEMA_VERSION:
                MIGRATIONS[step](self.conn)
                version = step
        if stored <= SCHEMA_VERSION and version != stored:
            # Persist the final version; never touch a store written by a
            # newer release (stored > SCHEMA_VERSION would be a downgrade).
            self.conn.execute(f"PRAGMA user_version = {version}")
        self.schema_version = version

    def close(self) -> None:
        self.conn.close()

    # ---- sessions ----

    def ensure_session(self, session_id: str, host: str, branch: str | None = None,
                       agent: str | None = None, phase: str | None = None) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO sessions (id, host, started_at, phase, branch, agent) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, host, _utcnow(), phase, branch, agent),
        )
        self.conn.commit()

    def end_session(self, session_id: str) -> None:
        self.conn.execute(
            "UPDATE sessions SET ended_at = ? WHERE id = ?", (_utcnow(), session_id)
        )
        self.conn.commit()

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return dict(row) if row else None

    # ---- raw events ----

    def add_event(self, event: dict[str, Any]) -> str | None:
        """Insert a raw event. Returns the event id, or None when it was not
        stored (duplicate id) — a duplicate is evidence already captured,
        not an error. Invalid shape still raises ValueError (programming error)."""
        if not event or not isinstance(event, dict):
            raise ValueError("Event must be a non-empty dictionary")
        if "type" not in event:
            raise ValueError("Event must have a 'type' field")

        eid = event.get("id") or f"evt-{self._mint_seq('evt')}"
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO events "
            "(id, type, session_id, ts, content, files, branch, meta, host)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                eid,
                event["type"],
                event.get("session_id"),
                event.get("ts") or _utcnow(),
                event.get("content"),
                json.dumps(event.get("files") or []),
                event.get("branch"),
                json.dumps(event.get("meta") or {}),
                event.get("host"),
            ),
        )
        return eid if cur.rowcount > 0 else None

    def undistilled_events(self, session_id: str | None = None) -> list[dict[str, Any]]:
        sql = "SELECT * FROM events WHERE distilled = 0"
        params: tuple = ()
        if session_id:
            sql += " AND session_id = ?"
            params = (session_id,)
        sql += " ORDER BY ts"
        rows = self.conn.execute(sql, params).fetchall()
        events = []
        for r in rows:
            e = dict(r)
            e["files"] = json.loads(e["files"] or "[]")
            e["meta"] = json.loads(e["meta"] or "{}")
            events.append(e)
        return events

    def all_events(self, session_id: str | None = None) -> list[dict[str, Any]]:
        """All events (distilled or not) — used by reviews and trace."""
        sql = "SELECT * FROM events"
        params: tuple = ()
        if session_id:
            sql += " WHERE session_id = ?"
            params = (session_id,)
        sql += " ORDER BY ts"
        rows = self.conn.execute(sql, params).fetchall()
        events = []
        for r in rows:
            e = dict(r)
            e["files"] = json.loads(e["files"] or "[]")
            e["meta"] = json.loads(e["meta"] or "{}")
            events.append(e)
        return events

    def mark_distilled(self, event_ids: list[str]) -> None:
        self.conn.executemany(
            "UPDATE events SET distilled = 1 WHERE id = ?", [(i,) for i in event_ids]
        )
        self.conn.commit()

    def purge_old_events(self, days: int, only_distilled: bool = True) -> int:
        """Raw events are evidence, not permanent memory (PRD §7.2). By default
        only events already distilled are purged, so no candidate knowledge is
        lost; provenance keeps its id references (granularity reduces)."""
        cutoff = (datetime.now(UTC) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        sql = "DELETE FROM events WHERE ts < ?"
        if only_distilled:
            sql += " AND distilled = 1"
        cur = self.conn.execute(sql, (cutoff,))
        self.conn.commit()
        return cur.rowcount

    # ---- entities ----

    def upsert(self, entity: Entity) -> None:
        if not entity or not hasattr(entity, 'id'):
            raise ValueError("Entity must be a valid Entity object with an id")

        # Entity row and FTS row must land together — a crash in between would
        # leave the entity invisible to search.
        with self._write_txn():
            self.conn.execute(
                "INSERT OR REPLACE INTO entities "
                "(id, type, status, authority, confidence, statement, details, scope, phase,"
                " session_id, provenance, freshness, superseded_by, created_at, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    entity.id,
                    entity.type.value,
                    entity.status.value,
                    entity.authority.value,
                    entity.confidence,
                    entity.statement,
                    json.dumps(entity.details, ensure_ascii=False),
                    json.dumps(entity.scope, ensure_ascii=False),
                    entity.phase,
                    entity.session_id,
                    entity.provenance.model_dump_json(),
                    entity.freshness.model_dump_json(),
                    entity.superseded_by,
                    entity.created_at,
                    entity.updated_at,
                ),
            )
            text = self._fts_text(entity)
            self.conn.execute("DELETE FROM entities_fts WHERE id = ?", (entity.id,))
            self.conn.execute(
                "INSERT INTO entities_fts (id, text) VALUES (?, ?)", (entity.id, text))

    @staticmethod
    def _fts_text(entity: Entity) -> str:
        parts = [entity.statement]
        for v in entity.details.values():
            if isinstance(v, str):
                parts.append(v)
            elif isinstance(v, list):
                parts.extend(str(x) for x in v)
        parts.extend(entity.scope)
        return " \n ".join(p for p in parts if p)

    def get(self, entity_id: str) -> Entity | None:
        if not entity_id or not isinstance(entity_id, str):
            return None
        row = self.conn.execute("SELECT * FROM entities WHERE id = ?", (entity_id,)).fetchone()
        return self._row_to_entity(row) if row else None

    def list_by_type(self, etype: ArtifactType, include_noncurrent: bool = True) -> list[Entity]:
        rows = self.conn.execute(
            "SELECT * FROM entities WHERE type = ? ORDER BY created_at", (etype.value,)
        ).fetchall()
        entities = [e for e in (self._row_to_entity(r) for r in rows) if e is not None]
        if not include_noncurrent:
            entities = [e for e in entities if e.is_current]
        return entities

    def all_entities(self) -> list[Entity]:
        rows = self.conn.execute("SELECT * FROM entities ORDER BY created_at").fetchall()
        return [e for e in (self._row_to_entity(r) for r in rows) if e is not None]

    def search(self, query: str, limit: int = 20) -> list[tuple[Entity, float]]:
        """FTS5-backed search returning (entity, score) where higher is better.

        The caller's limit is authoritative (clamped to MAX_SEARCH_LIMIT);
        the old behavior of silently rewriting limit>100 down to 20 crippled
        hybrid recall (compiler requests 200).
        """
        if not query or not isinstance(query, str):
            return []

        limit = max(1, min(int(limit), self.MAX_SEARCH_LIMIT))
            
        import re as _re
        tokens = _re.findall(r"[a-zA-Z0-9á-úà-ùâ-ûã-õçÁ-Ú_]+", query)
        fts_query = " OR ".join(f'"{t}"' for t in tokens[:12])
        if not fts_query:
            return []
        try:
            rows = self.conn.execute(
                "SELECT id, bm25(entities_fts) AS rank FROM entities_fts "
                "WHERE entities_fts MATCH ? ORDER BY rank LIMIT ?",
                (fts_query, limit),
            ).fetchall()
        except sqlite3.OperationalError:
            rows = []
        out: list[tuple[Entity, float]] = []
        for r in rows:
            ent = self.get(r["id"])
            if ent:
                out.append((ent, max(0.0, -r["rank"])))  # bm25: more negative = better
        return out

    def related(self, entity_id: str, rel: str | None = None,
                direction: str = "out") -> list[tuple[str, Entity]]:
        if direction == "out":
            sql, params = "SELECT rel, dst FROM edges WHERE src = ?", (entity_id,)
        elif direction == "in":
            sql, params = "SELECT rel, src FROM edges WHERE dst = ?", (entity_id,)
        else:
            sql, params = (
                "SELECT rel, dst FROM edges WHERE src = ? OR dst = ?", (entity_id, entity_id),
            )
        if rel:
            sql += " AND rel = ?"
            params += (rel,)
        out = []
        for r in self.conn.execute(sql, params).fetchall():
            target = r["dst"] if direction != "in" else r["src"]
            ent = self.get(target)
            if ent:
                out.append((r["rel"], ent))
        return out

    def add_edge(self, src: str, rel: str, dst: str) -> None:
        if not all([src, rel, dst]) or not all(isinstance(x, str) for x in [src, rel, dst]):
            raise ValueError("Edge parameters (src, rel, dst) must be non-empty strings")
        self.conn.execute(
            "INSERT OR IGNORE INTO edges (src, rel, dst, created_at) VALUES (?, ?, ?, ?)",
            (src, rel, dst, _utcnow()),
        )
        self.conn.commit()

    def edges_of(self, src: str | None = None, rel: str | None = None) -> list[dict[str, str]]:
        sql, params = "SELECT * FROM edges WHERE 1=1", []
        if src:
            sql += " AND src = ?"
            params.append(src)
        if rel:
            sql += " AND rel = ?"
            params.append(rel)
        return [dict(r) for r in self.conn.execute(sql, params).fetchall()]

    def node_degree(self, entity_id: str) -> int:
        """Returns total edge count (incoming + outgoing) for Knowledge Graph Density calculation."""
        row = self.conn.execute(
            "SELECT COUNT(*) as deg FROM edges WHERE src = ? OR dst = ?",
            (entity_id, entity_id),
        ).fetchone()
        return row["deg"] if row else 0


    def history(self, entity_id: str) -> list[dict[str, str]]:
        """Status transitions recorded as edges on the entity itself."""
        return self.edges_of(src=entity_id, rel="STATUS")

    def record_status_change(self, entity_id: str, from_status: str, to_status: str) -> None:
        self.add_edge(entity_id, "STATUS", f"{from_status}->{to_status}")

    # ---- governance helpers ----

    def set_status(self, entity_id: str, status: Status,
                   authority: Authority | None = None) -> Entity | None:
        ent = self.get(entity_id)
        if not ent:
            return None
        self.record_status_change(entity_id, ent.status.value, status.value)
        ent.status = status
        if authority is not None:
            ent.authority = authority
        if status == Status.ACTIVE:
            ent.freshness.last_verified_at = _utcnow()
            ent.freshness.stale = False
        ent.updated_at = _utcnow()
        self.upsert(ent)
        return ent

    def supersede(self, old_id: str, new_id: str) -> bool:
        old, new = self.get(old_id), self.get(new_id)
        if not old or not new:
            return False
        self.add_edge(new_id, "SUPERSEDES", old_id)
        self.set_status(old_id, Status.SUPERSEDED)
        old = self.get(old_id)
        old.superseded_by = new_id
        old.authority = Authority.SUPERSEDED
        self.upsert(old)
        # Negative knowledge survives supersession (PRD §44.4): rejected
        # alternatives of the old decision stay visible in the new one unless
        # explicitly contradicted.
        old_alts = old.details.get("alternatives_rejected") or []
        if old_alts:
            new_alts = list(dict.fromkeys(
                (new.details.get("alternatives_rejected") or []) + old_alts))
            new.details["alternatives_rejected"] = new_alts
            self.upsert(new)
        if new.status in (Status.CANDIDATE, Status.PROPOSED):
            self.set_status(new_id, Status.ACTIVE)
        return True

    # ---- stats ----

    def stats(self) -> dict[str, Any]:
        entities = self.all_entities()
        by_type: dict[str, int] = {}
        for e in entities:
            by_type[e.type.value] = by_type.get(e.type.value, 0) + 1
        ev = self.conn.execute("SELECT COUNT(*) c FROM events").fetchone()["c"]
        sess = self.conn.execute("SELECT COUNT(*) c FROM sessions").fetchone()["c"]
        return {"entities": by_type, "total_entities": len(entities),
                "raw_events": ev, "sessions": sess}

    # ---- distillation runs (observability, PRD §41) ----

    def record_distill_run(self, session_id: str | None, summary: str) -> None:
        self.conn.execute(
            "INSERT INTO distill_runs (ts, session, summary) VALUES (?, ?, ?)",
            (_utcnow(), session_id, summary),
        )
        self.conn.commit()

    def last_distill_runs(self, n: int = 3) -> list[dict[str, str]]:
        rows = self.conn.execute(
            "SELECT * FROM distill_runs ORDER BY ts DESC LIMIT ?", (n,)
        ).fetchall()
        return [dict(r) for r in rows]

    # ---- internals ----

    def _mint_seq(self, prefix: str) -> int:
        """Atomic id mint: single-statement UPSERT+RETURNING inside an
        IMMEDIATE transaction — safe across the three concurrent writer
        processes (CLI, MCP server, hook subprocess)."""
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            row = self.conn.execute(
                "INSERT INTO entity_seq (prefix, last) VALUES (?, 1) "
                "ON CONFLICT(prefix) DO UPDATE SET last = last + 1 "
                "RETURNING last",
                (prefix,),
            ).fetchone()
            nxt = int(row[0])
            self.conn.execute("COMMIT")
            return nxt
        except Exception:
            self.conn.execute("ROLLBACK")
            raise

    def _next_int(self, prefix: str) -> int:
        return self._mint_seq(prefix)

    def reserve_entity_id(self, etype: ArtifactType) -> str:
        return f"{_PREFIX_BY_TYPE[etype]}-{self._mint_seq(etype.value):04d}"

    def _row_to_entity(self, row: sqlite3.Row) -> Entity | None:
        """Degrade with signal (Principle 1): one malformed row must never
        poison every reader — skip it, count it, log the id."""
        from cortex.knowledge.models import Freshness, Provenance
        try:
            return Entity(
                id=row["id"],
                type=ArtifactType(row["type"]),
                statement=row["statement"],
                status=Status(row["status"]),
                authority=Authority(row["authority"]),
                confidence=row["confidence"],
                scope=json.loads(row["scope"] or "[]"),
                phase=row["phase"],
                session_id=row["session_id"],
                details=json.loads(row["details"] or "{}"),
                provenance=Provenance.model_validate_json(row["provenance"] or "{}"),
                freshness=Freshness.model_validate_json(row["freshness"] or "{}"),
                superseded_by=row["superseded_by"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
        except Exception as exc:
            self.malformed_rows += 1
            logging.getLogger("cortex.store").error(
                "malformed entity row skipped: id=%s err=%s", row["id"], exc)
            return None
