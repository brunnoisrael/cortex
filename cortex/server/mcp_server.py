"""Cortex MCP Server (PRD §20) — stdio, local-first.

Run with:  python -m cortex.server.mcp_server
"""

from __future__ import annotations

import json
import os
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP  # mcp<2 (also mcp>=1.0,<3.0's older releases)
except ImportError:
    # mcp>=2.0 renamed FastMCP -> MCPServer, moved to mcp.server.mcpserver.
    # (There never was an `mcp.server.FastMCP`; that branch was dead in every
    # released version of the SDK and has been removed here — see
    # PLANO_ENDURECIMENTO_2026-09-08.md item 5.6 for the verification.)
    from mcp.server.mcpserver import MCPServer as FastMCP  # type: ignore

from cortex.capture.recorder import capture_event
from cortex.compiler.compiler import CompileInput, compile_context, rank
from cortex.config import CortexConfig, CortexConfigError
from cortex.distillation.engine import DistillationEngine
from cortex.distillation.review import build_session_review
from cortex.knowledge.models import (
    ArtifactType,
    Authority,
    Entity,
    Provenance,
    Status,
    session_id_for,
)
from cortex.storage.store import KnowledgeStore
from cortex.workspace import Workspace, detect_workspace, ensure_cortex_dir

mcp = FastMCP("cortex")


def _ws() -> tuple[Workspace, CortexConfig]:
    """Resolve the workspace strictly (Onda 1, P0.3): CORTEX_ROOT wins; the
    cwd fallback only accepts directories that were actually initialized
    (cortex.toml or .cortex present) — never an unrelated repository."""
    root = os.environ.get("CORTEX_ROOT")
    if root:
        ws = detect_workspace(Path(root))
        if ws is None:
            raise RuntimeError(f"no workspace found at CORTEX_ROOT={root}")
    else:
        ws = detect_workspace(Path.cwd())
        initialized = ws is not None and (
            (ws.root / "cortex.toml").exists() or (ws.root / ".cortex").exists()
        )
        if not initialized:
            raise RuntimeError(
                "Cortex workspace not detected. Run `cortex init` or set CORTEX_ROOT."
            )
    try:
        return ws, CortexConfig.load(ws.root)
    except CortexConfigError as exc:
        # Surfaced as a readable tool error to the agent, not a bare traceback.
        raise RuntimeError(str(exc)) from exc


# Store cached per workspace (item 5.6): the MCP server is a single
# long-lived process handling many tool calls against the same workspace,
# so re-opening KnowledgeStore (full executescript DDL + WAL setup) on
# every single call was pure overhead. The connection is created once and
# reused; tools no longer call store.close() at the end of each call — a
# stray close() would still be harmless (KnowledgeStore.close() is
# idempotent per Onda 5.1) but nothing calls it anymore in the normal path.
_stores: dict[str, KnowledgeStore] = {}


def _store() -> tuple[Workspace, CortexConfig, KnowledgeStore]:
    ws, cfg = _ws()
    key = str(ws.db_path)
    if key not in _stores:
        ensure_cortex_dir(ws)
        _stores[key] = KnowledgeStore(ws.db_path)
    return ws, cfg, _stores[key]


def _invalid_kind_error(kind: str, extra: tuple[str, ...] = ()) -> str:
    """Item 5.6: ArtifactType(kind) on a bad value used to raise a bare
    ValueError straight out of the tool call. Returned as ordinary tool
    output instead, so the agent gets an actionable message it can act on
    (e.g. retry with a valid kind) rather than an opaque tool-call error."""
    valid = ", ".join((*extra, *sorted(t.value for t in ArtifactType)))
    return json.dumps({"ok": False, "error": f"invalid kind {kind!r}; use one of: {valid}"})


@mcp.tool()
def cortex_init(branch: str = "", task: str = "") -> str:
    """Session bootstrap: returns the compiled CORTEX CONTEXT block for the
    current branch/task within the configured token budget."""
    _ws, cfg, store = _store()
    session_id = session_id_for("mcp")
    store.ensure_session(session_id, host="mcp", branch=branch or None)
    return compile_context(
        store,
        CompileInput(query=task, branch=branch or None, phase=cfg.phase),
        max_tokens=cfg.context_max_tokens,
        max_adrs=cfg.max_adrs,
        max_intentions=cfg.max_intentions,
        max_correndas=cfg.max_correndas,
    )


@mcp.tool()
def cortex_recall(query: str, scope: list[str] | None = None,
                  include_provenance: bool = False, max_results: int = 10) -> str:
    """Retrieve relevant engineering knowledge for the current task."""
    _, _, store = _store()
    items = rank(store, CompileInput(query=query, files=scope), limit=max_results)
    out = []
    for item in items:
        e = item.entity
        entry = {
            "id": e.id, "type": e.type.value, "statement": e.statement,
            "status": e.status.value, "authority": e.authority.value,
            "confidence": e.confidence, "scope": e.scope, "score": item.score,
        }
        if include_provenance:
            entry["provenance"] = e.provenance.model_dump()
        out.append(entry)
    return json.dumps(out, ensure_ascii=False, indent=2)


@mcp.tool()
def cortex_remember(statement: str, kind: str = "intention", motivation: str = "",
                    scope: list[str] | None = None) -> str:
    """Explicitly record knowledge: kind = intention | adr | correnda."""
    _, _, store = _store()
    try:
        etype = ArtifactType(kind)
    except ValueError:
        return _invalid_kind_error(kind)
    eid = store.reserve_entity_id(etype)
    ent_type_map = {
        "intention": {"motivation": motivation},
        "adr": {"context": motivation, "decision": statement, "alternatives_rejected": []},
        "correnda": {"rule": statement, "origin": [], "confirmed_by_human": True},
    }
    ent = Entity(
        id=eid, type=etype, statement=statement,
        status=Status.ACTIVE, authority=Authority.HUMAN_CONFIRMED, confidence=0.95,
        scope=scope or [], session_id=session_id_for("mcp"),
        details=ent_type_map.get(kind, {}),
        provenance=Provenance(extraction_source="explicit_user_statement"),
    )
    store.upsert(ent)
    return f"recorded {eid} ({kind}, human_confirmed)"


@mcp.tool()
def cortex_emit(
    kind: str,
    statement: str,
    rationale: str = "",
    alternatives_rejected: list[str] | None = None,
    scope: list[str] | None = None,
    confidence_self_reported: float = 0.95,
) -> str:
    """Agent native knowledge emission (Onda 6).

    Directly register an architectural decision (adr), intention, bug fix,
    or negative knowledge (correnda) with high confidence as the agent works.

    kind: 'adr' | 'intention' | 'fix' | 'correnda' | 'negative_knowledge'
    """
    _, _, store = _store()
    type_str = "correnda" if kind == "negative_knowledge" else kind
    try:
        etype = ArtifactType(type_str)
    except ValueError:
        return _invalid_kind_error(kind, extra=("negative_knowledge",))
    eid = store.reserve_entity_id(etype)

    details: dict = {}
    if kind == "adr":
        details = {
            "context": rationale,
            "decision": statement,
            "alternatives_rejected": alternatives_rejected or [],
        }
    elif kind in ("correnda", "negative_knowledge"):
        details = {
            "rule": statement,
            "rationale": rationale,
            "origin": ["cortex_emit"],
            "confirmed_by_human": False,
        }
    elif kind == "intention":
        details = {"motivation": rationale or statement}
    elif kind == "fix":
        details = {"problem": statement, "solution": rationale}

    conf = max(0.1, min(1.0, confidence_self_reported))
    status = Status.ACTIVE if kind == "fix" else Status.PROPOSED
    authority = Authority.AGENT_INFERRED

    ent = Entity(
        id=eid,
        type=etype,
        statement=statement,
        status=status,
        authority=authority,
        confidence=conf,
        scope=scope or [],
        session_id=session_id_for("mcp"),
        details=details,
        provenance=Provenance(extraction_source="cortex_emit_mcp_tool"),
    )
    store.upsert(ent)
    return f"emitted {eid} ({kind}, status={status.value}, confidence={conf})"


@mcp.tool()
def cortex_capture(event_type: str, content: str, session_id: str = "",
                   files: list[str] | None = None) -> str:
    """Capture a raw session event (user_instruction, agent_response, error,
    test_failure, commit, tool_result). Redaction runs before persistence."""
    _, _, store = _store()
    session_id = session_id or session_id_for("mcp")
    store.ensure_session(session_id, host="mcp")
    eid = capture_event(store, {
        "type": event_type, "session_id": session_id, "content": content,
        "files": files or [],
    })
    return f"captured {eid}"


@mcp.tool()
def cortex_distill(session_id: str = "") -> str:
    """Run distillation over captured events (session or all)."""
    _, cfg, store = _store()
    engine = DistillationEngine(
        store,
        min_confidence=cfg.min_confidence_for_persistence,
        correnda_min_evidence=cfg.correnda_min_evidence,
        retention_days=cfg.raw_retention_days,
        llm=cfg.llm,
        ollama_url=cfg.ollama_url,
        llm_model=cfg.llm_model,
        llm_timeout_s=cfg.llm_timeout_s,
        network_calls=cfg.network_calls,
    )
    report = engine.distill_session(session_id) if session_id else engine.distill_all()
    return report.summary() + (" | new: " + ", ".join(report.new_ids) if report.new_ids else "")


@mcp.tool()
def cortex_review(session_id: str = "") -> str:
    """Generate a structured session review (produced/unresolved/risks)."""
    _, _, store = _store()
    if not session_id:
        rows = store.conn.execute(
            "SELECT id FROM sessions WHERE ended_at IS NULL ORDER BY started_at DESC LIMIT 1"
        ).fetchall()
        if not rows:
            return "no open session"
        session_id = rows[0]["id"]
    rev = build_session_review(store, session_id)
    return json.dumps(rev.details, ensure_ascii=False, indent=2) if rev else f"session {session_id} not found"


@mcp.tool()
def cortex_status() -> str:
    """Store statistics and health."""
    _, cfg, store = _store()
    return json.dumps({"config": {"max_tokens": cfg.context_max_tokens,
                                  "privacy_local_only": not cfg.network_calls},
                       **store.stats()}, ensure_ascii=False, indent=2)


@mcp.tool()
def cortex_verify(entity_id: str) -> str:
    """Verify a memory against the repository: cited symbols must exist in
    scope files for repository_verified promotion (PRD §47)."""
    ws, _, store = _store()
    ent = store.get(entity_id)
    if not ent:
        return f"{entity_id} not found"
    from cortex.verification import verify_entity
    result = verify_entity(store, ws.root, ent)
    return json.dumps(result, ensure_ascii=False)


@mcp.tool()
def cortex_phase() -> str:
    """Phase review: long-range knowledge health indicators (PRD §13.2)."""
    _, _, store = _store()
    ents = store.all_entities()
    adrs = [e for e in ents if e.type == ArtifactType.ADR]
    correndas = [e for e in ents if e.type == ArtifactType.CORRENDA]
    return json.dumps({
        "adr_total": len(adrs),
        "adr_candidates": len([e for e in adrs if e.status == Status.CANDIDATE]),
        "superseded": len([e for e in ents if e.status == Status.SUPERSEDED]),
        "correndas_active": len([c for c in correndas if c.status == Status.ACTIVE]),
        "correndas_proposed": len([c for c in correndas if c.status == Status.PROPOSED]),
        "stale": len([e for e in ents if e.freshness.stale]),
        "total_entities": len(ents),
    }, ensure_ascii=False, indent=2)


def _list_artifacts(store: KnowledgeStore, etype: ArtifactType) -> str:
    ents = store.list_by_type(etype)
    return json.dumps([{
        "id": e.id, "statement": e.statement, "status": e.status.value,
        "authority": e.authority.value, "confidence": e.confidence, "scope": e.scope,
    } for e in ents], ensure_ascii=False, indent=2)


@mcp.tool()
def cortex_intention() -> str:
    """List recorded Intentions (PRD §20.2)."""
    _, _, store = _store()
    return _list_artifacts(store, ArtifactType.INTENTION)


@mcp.tool()
def cortex_adr() -> str:
    """List ADRs (PRD §20.2)."""
    _, _, store = _store()
    return _list_artifacts(store, ArtifactType.ADR)


@mcp.tool()
def cortex_fix() -> str:
    """List Fixes (PRD §20.2)."""
    _, _, store = _store()
    return _list_artifacts(store, ArtifactType.FIX)


@mcp.tool()
def cortex_correnda() -> str:
    """List Correndas with their lifecycle status (PRD §20.2)."""
    _, _, store = _store()
    return _list_artifacts(store, ArtifactType.CORRENDA)


@mcp.tool()
def cortex_diff(last_n_sessions: int = 2) -> str:
    """Summarize what changed in knowledge across the last N sessions."""
    _, _, store = _store()
    # SQLite treats a negative LIMIT as "no limit" — clamp so a stray -1
    # can't dump the entire session history instead of a bounded window.
    last_n_sessions = max(1, last_n_sessions)
    rows = store.conn.execute(
        "SELECT id, started_at FROM sessions ORDER BY started_at DESC LIMIT ?",
        (last_n_sessions,),
    ).fetchall()
    out = {}
    for r in rows:
        ents = [e for e in store.all_entities() if e.session_id == r["id"]]
        out[r["id"]] = {
            "started_at": r["started_at"],
            "artifacts": {e.id: e.statement[:80] for e in ents},
        }
    return json.dumps(out, ensure_ascii=False, indent=2)


@mcp.tool()
def cortex_why(entity_id: str) -> str:
    """Explain a memory: statement, evidence, provenance, authority (PRD §50)."""
    _, _, store = _store()
    ent = store.get(entity_id)
    if not ent:
        return f"{entity_id} not found"
    evidence = [
        {"rel": rel, "id": t.id, "type": t.type.value, "statement": t.statement}
        for rel, t in store.related(ent.id, direction="in")
    ] + [
        {"rel": rel, "id": t.id, "type": t.type.value}
        for rel, t in store.related(ent.id, direction="out")
    ]
    return json.dumps({
        "id": ent.id, "type": ent.type.value, "statement": ent.statement,
        "status": ent.status.value, "authority": ent.authority.value,
        "confidence": ent.confidence, "details": ent.details,
        "provenance": ent.provenance.model_dump(), "evidence": evidence,
    }, ensure_ascii=False, indent=2)
