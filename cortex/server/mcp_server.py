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
from cortex.distillation.review import build_session_review
from cortex.governance import review_queue
from cortex.knowledge.models import (
    ArtifactType,
    Authority,
    Entity,
    Provenance,
    ReviewPolicy,
    RiskLevel,
    Status,
    _utcnow,
    session_id_for,
)
from cortex.service import (
    build_distillation_engine,
    latest_open_session_id,
    phase_health,
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
            "risk_level": e.risk_level.value, "review_policy": e.review_policy.value,
        }
        if include_provenance:
            entry["provenance"] = e.provenance.model_dump()
        out.append(entry)
    return json.dumps(out, ensure_ascii=False, indent=2)


@mcp.tool()
def cortex_remember(statement: str, kind: str = "intention", motivation: str = "",
                    scope: list[str] | None = None,
                    risk_level: str = "medium",
                    review_policy: str = "multiple_evidence") -> str:
    """Explicitly record knowledge: kind = intention | adr | correnda.

    This tool is invoked by the agent, so nothing here can verify a human
    was in the loop — recorded knowledge is agent_inferred and PROPOSED,
    exactly like cortex_emit. Human confirmation stays a CLI governance
    action (`cortex correnda confirm` / `cortex adrs accept`)."""
    _, _, store = _store()
    try:
        etype = ArtifactType(kind)
    except ValueError:
        return _invalid_kind_error(kind)
    try:
        risk = RiskLevel(risk_level)
        policy = ReviewPolicy(review_policy)
    except ValueError:
        return json.dumps({"ok": False, "error": "invalid risk_level or review_policy"})
    eid = store.reserve_entity_id(etype)
    ent_type_map = {
        "intention": {"motivation": motivation},
        "adr": {"context": motivation, "decision": statement, "alternatives_rejected": []},
        "correnda": {"rule": statement, "origin": [], "confirmed_by_human": False},
    }
    ent = Entity(
        id=eid, type=etype, statement=statement,
        status=Status.PROPOSED, authority=Authority.AGENT_INFERRED, confidence=0.85,
        scope=scope or [], session_id=session_id_for("mcp"),
        risk_level=risk, review_policy=policy,
        details=ent_type_map.get(kind, {}),
        provenance=Provenance(extraction_source="explicit_agent_statement"),
    )
    ent.details["extraction_method"] = "cortex_remember"
    store.upsert(ent)
    return f"recorded {eid} ({kind}, proposed — confirm via CLI governance to activate)"


@mcp.tool()
def cortex_emit(
    kind: str,
    statement: str,
    rationale: str = "",
    alternatives_rejected: list[str] | None = None,
    scope: list[str] | None = None,
    confidence_self_reported: float = 0.95,
    risk_level: str = "medium",
    review_policy: str = "multiple_evidence",
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
    try:
        risk = RiskLevel(risk_level)
        policy = ReviewPolicy(review_policy)
    except ValueError:
        return json.dumps({"ok": False, "error": "invalid risk_level or review_policy"})
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
    details["extraction_method"] = "cortex_emit"

    conf = max(0.1, min(1.0, confidence_self_reported))
    status = Status.ACTIVE if kind == "fix" and risk != RiskLevel.HIGH else Status.PROPOSED
    authority = Authority.AGENT_INFERRED

    ent = Entity(
        id=eid,
        type=etype,
        statement=statement,
        status=status,
        authority=authority,
        confidence=conf,
        scope=scope or [],
        risk_level=risk, review_policy=policy,
        observed_at=_utcnow(),
        valid_from=_utcnow()
        if status == Status.ACTIVE else None,
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
    engine = build_distillation_engine(store, cfg)
    report = engine.distill_session(session_id) if session_id else engine.distill_all()
    return report.summary() + (" | new: " + ", ".join(report.new_ids) if report.new_ids else "")


@mcp.tool()
def cortex_review(session_id: str = "") -> str:
    """Generate a structured session review (produced/unresolved/risks)."""
    _, _, store = _store()
    if not session_id:
        session_id = latest_open_session_id(store) or ""
        if not session_id:
            return "no open session"
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
    return json.dumps(phase_health(store), ensure_ascii=False, indent=2)


DEFAULT_LIST_LIMIT = 50
MAX_LIST_LIMIT = 200


def _list_artifacts(store: KnowledgeStore, etype: ArtifactType, limit: int = DEFAULT_LIST_LIMIT) -> str:
    """Bounded listing (item: MCP listing limits). These tools used to
    return every entity of a type with no cap — an agent calling
    cortex_adr() on a store with thousands of ADRs got them all dumped into
    its context in one tool result. Most-recently-created entities are the
    ones an agent working right now is most likely to need, so a capped
    call keeps those and reports the true total so the agent knows it was
    truncated (and can ask for more, up to MAX_LIST_LIMIT, if it needs to)."""
    limit = max(1, min(int(limit), MAX_LIST_LIMIT))
    ents = store.list_by_type(etype)
    total = len(ents)
    ents = sorted(ents, key=lambda e: e.created_at, reverse=True)[:limit]
    return json.dumps({
        "total": total,
        "returned": len(ents),
        "items": [{
            "id": e.id, "statement": e.statement, "status": e.status.value,
            "authority": e.authority.value, "confidence": e.confidence, "scope": e.scope,
            "risk_level": e.risk_level.value, "review_policy": e.review_policy.value,
        } for e in ents],
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def cortex_intention(limit: int = DEFAULT_LIST_LIMIT) -> str:
    """List recorded Intentions, most recent first (PRD §20.2). Capped at
    `limit` (default 50, max 200); the result's `total` field says how many
    exist in the store even when truncated."""
    _, _, store = _store()
    return _list_artifacts(store, ArtifactType.INTENTION, limit)


@mcp.tool()
def cortex_adr(limit: int = DEFAULT_LIST_LIMIT) -> str:
    """List ADRs, most recent first (PRD §20.2). Capped at `limit` (default
    50, max 200); the result's `total` field says how many exist in the
    store even when truncated."""
    _, _, store = _store()
    return _list_artifacts(store, ArtifactType.ADR, limit)


@mcp.tool()
def cortex_fix(limit: int = DEFAULT_LIST_LIMIT) -> str:
    """List Fixes, most recent first (PRD §20.2). Capped at `limit`
    (default 50, max 200); the result's `total` field says how many exist
    in the store even when truncated."""
    _, _, store = _store()
    return _list_artifacts(store, ArtifactType.FIX, limit)


@mcp.tool()
def cortex_correnda(limit: int = DEFAULT_LIST_LIMIT) -> str:
    """List Correndas with their lifecycle status, most recent first (PRD
    §20.2). Capped at `limit` (default 50, max 200); the result's `total`
    field says how many exist in the store even when truncated."""
    _, _, store = _store()
    return _list_artifacts(store, ArtifactType.CORRENDA, limit)


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
        ents = store.entities_by_session(r["id"])
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
        "extraction": ent.provenance.extraction_source,
        "status": ent.status.value, "authority": ent.authority.value,
        "confidence": ent.confidence, "details": ent.details,
        "provenance": ent.provenance.model_dump(), "evidence": evidence,
        "evidence_ledger": [item.model_dump(mode="json") for item in ent.evidence],
        "governance_receipts": store.governance_receipts(entity_id),
        "decision_history": store.decision_history(entity_id),
        "last_verification": {
            "at": ent.freshness.last_verified_at,
            "source": ent.freshness.verification_source,
            "stale": ent.freshness.stale,
        },
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def cortex_retrieval_trace(task: str = "", files: list[str] | None = None,
                           limit: int = 20, budget: int | None = None) -> str:
    """Return stable signals, rankings and exclusion reasons for a retrieval."""
    from cortex.compiler.compiler import retrieval_trace
    _, cfg, store = _store()
    return json.dumps(retrieval_trace(
        store, CompileInput(query=task, files=files), limit=limit,
        budget=budget or cfg.context_max_tokens,
    ), ensure_ascii=False, indent=2)


@mcp.tool()
def cortex_review_queue() -> str:
    """List proposed, high-risk and contradictory artifacts awaiting review."""
    _, _, store = _store()
    return json.dumps([{
        "id": entity.id, "type": entity.type.value, "statement": entity.statement,
        "status": entity.status.value, "risk_level": entity.risk_level.value,
        "review_policy": entity.review_policy.value,
        "contradiction_pending": bool(entity.details.get("contradiction_pending")),
    } for entity in review_queue(store)], ensure_ascii=False, indent=2)


@mcp.tool()
def cortex_evidence_export(entity_id: str) -> str:
    """Return a reproducible evidence package for one artifact."""
    from cortex.knowledge.evidence import export_evidence_package
    _, _, store = _store()
    try:
        return json.dumps(export_evidence_package(store, entity_id), ensure_ascii=False, indent=2)
    except ValueError as exc:
        return json.dumps({"ok": False, "error": str(exc)})


@mcp.tool()
def cortex_review_attach(base: str = "HEAD", commit: str = "", pull_request: str = "",
                         files: list[str] | None = None) -> str:
    """Create an auditable impact review for a diff, commit or PR reference."""
    from cortex.engineering_review import build_review_summary, review_as_dict
    ws, _, store = _store()
    review = build_review_summary(
        store, ws.root, base=base, commit=commit or None,
        pull_request=pull_request or None, paths=files,
    )
    return json.dumps(review_as_dict(store, review.id), ensure_ascii=False, indent=2)


@mcp.tool()
def cortex_review_summary(review_id: str) -> str:
    """Return decisions, rules, conflicts and missing evidence for a review."""
    from cortex.engineering_review import review_as_dict
    _, _, store = _store()
    try:
        return json.dumps(review_as_dict(store, review_id), ensure_ascii=False, indent=2)
    except ValueError as exc:
        return json.dumps({"ok": False, "error": str(exc)})


@mcp.tool()
def cortex_store_export() -> str:
    """Return the complete versioned portable store package."""
    from cortex.portable import export_store
    _, _, store = _store()
    return json.dumps(export_store(store), ensure_ascii=False, indent=2, sort_keys=True)
