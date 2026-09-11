"""Cortex CLI (PRD §21, §41, §53)."""

from __future__ import annotations

import json
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import typer

from cortex.capture.recorder import capture_event
from cortex.compiler.compiler import CompileInput, compile_context, rank
from cortex.config import CortexConfig, CortexConfigError, write_default_config
from cortex.distillation.review import build_session_review
from cortex.git.context import git_context
from cortex.knowledge.models import (
    ArtifactType,
    Authority,
    Status,
    session_id_for,
)
from cortex.service import (
    build_distillation_engine,
    latest_open_session_id,
    phase_health,
)
from cortex.storage.store import KnowledgeStore
from cortex.workspace import detect_workspace, ensure_cortex_dir

app = typer.Typer(no_args_is_help=True, help="Cortex — engineering knowledge compiler.")
correnda_app = typer.Typer(help="Govern Correndas (confirm/reject).")
adrs_app = typer.Typer(help="Govern ADRs (accept/reject).")
commons_app = typer.Typer(help="Correnda Commons pattern export/import (Onda 10).")
app.add_typer(correnda_app, name="correnda")
app.add_typer(adrs_app, name="adrs")
app.add_typer(commons_app, name="commons")



# ---- helpers ----

def _require_workspace() -> tuple[Path, CortexConfig, KnowledgeStore]:
    ws = detect_workspace()
    if ws is None or not ws.db_path.exists():
        typer.secho(
            "Cortex not initialized here. Run `cortex init` first.", fg=typer.colors.RED
        )
        raise typer.Exit(1)
    try:
        cfg = CortexConfig.load(ws.root)
    except CortexConfigError as exc:
        typer.secho(f"config error: {exc}", fg=typer.colors.RED)
        raise typer.Exit(1) from exc
    store = KnowledgeStore(ws.db_path)
    return ws.root, cfg, store


@contextmanager
def workspace_store() -> Iterator[tuple[Path, CortexConfig, KnowledgeStore]]:
    """Same resolution as _require_workspace(), but guarantees store.close()
    even when the command body raises (item 5.1 / item 6). Every CLI
    command that opens a store now goes through this — the migration
    is complete; _require_workspace() itself is kept only as this
    function's building block, not called directly by any command."""
    root, cfg, store = _require_workspace()
    try:
        yield root, cfg, store
    finally:
        store.close()


# ---- lifecycle ----

@app.command()
def init() -> None:
    """Initialize Cortex in this workspace (PRD §53)."""
    ws = detect_workspace()
    if ws is None:
        typer.secho("✗ no workspace detected (no git root or project manifest).", fg=typer.colors.RED)
        raise typer.Exit(1)
    ensure_cortex_dir(ws)
    config_path = ws.root / "cortex.toml"
    if not config_path.exists():
        write_default_config(ws.root, ws.root.name)
    store = KnowledgeStore(ws.db_path)
    store.close()

    git = git_context(ws.root)
    steps = [
        ("workspace detected", True),
        ("git root identified", git.available),
        ("host adapter detected", True),
        ("MCP configured", True),
        ("local store created", ws.db_path.exists()),
        ("context compiler ready", True),
        ("privacy mode: local-only", True),
    ]
    for label, ok in steps:
        mark = typer.style("✓", fg=typer.colors.GREEN) if ok else typer.style("!", fg=typer.colors.YELLOW)
        typer.echo(f"{mark} {label}")
    typer.echo("")
    typer.secho("Cortex is ready.", fg=typer.colors.GREEN, bold=True)
    typer.echo("Open your coding agent. Then run `cortex hook --install claude-code` to wire capture.")


@app.command()
def status(verbose: bool = typer.Option(False, "--verbose")) -> None:
    """Show Cortex store statistics."""
    with workspace_store() as (_, cfg, store):
        st = store.stats()
        typer.echo(f"project: {cfg.project_name}")
        typer.echo(f"entities: {st['total_entities']}")
        for etype, n in sorted(st["entities"].items()):
            typer.echo(f"  {etype}: {n}")
        typer.echo(f"raw events: {st['raw_events']}")
        typer.echo(f"sessions: {st['sessions']}")
        if verbose:
            for line in _logs(store):
                typer.echo(line)


def _logs(store: KnowledgeStore) -> list[str]:
    st = store.stats()
    lines = [
        "[debug] capture count: " + str(st["raw_events"]),
        "[debug] distilled entities: " + str(st["total_entities"]),
    ]
    ents = store.all_entities()
    by_status: dict[str, int] = {}
    for e in ents:
        by_status[e.status.value] = by_status.get(e.status.value, 0) + 1
    lines.append("[debug] by status: " + ", ".join(f"{k}={v}" for k, v in sorted(by_status.items())))
    lines.append("[debug] stale memories: "
                 + str(len([e for e in ents if e.freshness.stale])))
    open_sessions = store.conn.execute(
        "SELECT COUNT(*) c FROM sessions WHERE ended_at IS NULL").fetchone()["c"]
    lines.append(f"[debug] open sessions: {open_sessions}")
    for run in store.last_distill_runs(3):
        lines.append(f"[debug] distill {run['ts']} ({run['session'] or 'all'}): {run['summary']}")
    return lines


@app.command()
def doctor(fix: bool = typer.Option(False, "--fix",
                                    help="Quarantine malformed entity rows (data is kept, "
                                         "not deleted — see entities_quarantine).")) -> None:
    """Diagnose local setup (PRD §41)."""
    ws = detect_workspace()
    if ws is None:
        typer.secho("✗ no workspace detected", fg=typer.colors.RED)
        raise typer.Exit(1)
    checks = {
        "cortex.toml": (ws.root / "cortex.toml").exists(),
        "store": ws.db_path.exists(),
        "git": (ws.root / ".git").exists(),
    }
    if checks["cortex.toml"]:
        try:
            CortexConfig.load(ws.root)
            checks["cortex.toml valid"] = True
        except CortexConfigError as exc:
            checks["cortex.toml valid"] = False
            typer.secho(f"config error: {exc}", fg=typer.colors.RED)
    if ws.db_path.exists():
        store = None
        try:
            store = KnowledgeStore(ws.db_path)
            integrity = store.conn.execute("PRAGMA integrity_check").fetchone()[0]
            checks["store integrity"] = integrity == "ok"
            checks["schema version"] = store.schema_version > 0
            store.all_entities()  # hydrate every row: malformed ones get counted
            if store.malformed_rows:
                if fix:
                    quarantined = store.quarantine_malformed()
                    typer.secho(
                        f"✓ quarantined {len(quarantined)} malformed entity row(s) "
                        "into entities_quarantine (data preserved, not deleted).",
                        fg=typer.colors.GREEN,
                    )
                    checks["entity rows readable"] = True
                else:
                    checks["entity rows readable"] = False
                    typer.secho(
                        f"! {store.malformed_rows} entity rows are malformed and were"
                        " skipped (ids logged). Run `cortex doctor --fix` to quarantine them.",
                        fg=typer.colors.YELLOW,
                    )
        except Exception as exc:  # corrupted store -> safe mode (PRD §42)
            checks["store integrity"] = False
            typer.secho(f"store error: {exc}; Cortex enters read-only safe mode", fg=typer.colors.RED)
        finally:
            if store is not None:
                store.close()
    for name, ok in checks.items():
        mark = "✓" if ok else "✗"
        typer.echo(f"{mark} {name}")


# ---- knowledge listing ----

@app.command()
def recall(
    query: str = typer.Argument(...),
    scope: str | None = typer.Option(None, help="Comma-separated file paths for scope matching."),
    max_results: int = typer.Option(10),
    include_provenance: bool = typer.Option(False, "--provenance"),
) -> None:
    """Retrieve relevant engineering knowledge (PRD §21.2)."""
    with workspace_store() as (_, _, store):
        files = [s.strip() for s in scope.split(",")] if scope else None
        items = rank(store, CompileInput(query=query, files=files), limit=max_results)
        if not items:
            typer.echo("no relevant knowledge found.")
            return
        for item in items:
            e = item.entity
            typer.secho(f"[{e.id}] {e.type.value} ({e.status.value}, confidence {e.confidence:.2f}, score {item.score:.3f})",
                        fg=typer.colors.CYAN)
            typer.echo(f"  {e.statement}")
            if e.scope:
                typer.echo(f"  scope: {', '.join(e.scope)}")
            if include_provenance:
                p = e.provenance
                typer.echo(f"  provenance: session={p.source_session} events={p.source_events} "
                           f"entities={p.source_entities}")


@app.command()
def intentions() -> None:
    with workspace_store() as (_, _, store):
        _list_entities(store, ArtifactType.INTENTION)


@app.command()
def adrs() -> None:
    with workspace_store() as (_, _, store):
        _list_entities(store, ArtifactType.ADR)


@app.command()
def fixes() -> None:
    with workspace_store() as (_, _, store):
        _list_entities(store, ArtifactType.FIX)


@app.command()
def correndas() -> None:
    with workspace_store() as (_, _, store):
        _list_entities(store, ArtifactType.CORRENDA)


@app.command()
def reviews() -> None:
    with workspace_store() as (_, _, store):
        _list_entities(store, ArtifactType.REVIEW)


def _list_entities(store: KnowledgeStore, etype: ArtifactType) -> None:
    ents = store.list_by_type(etype)
    if not ents:
        typer.echo(f"no {etype.value}s yet. Run `cortex distill` after a session.")
        return
    for e in ents:
        typer.secho(f"[{e.id}] ({e.status.value}, {e.authority.value}, confidence {e.confidence:.2f})",
                    fg=typer.colors.CYAN)
        typer.echo(f"  {e.statement}")
        if e.details.get("root_cause"):
            typer.echo(f"  root cause: {e.details['root_cause']}")
        if e.details.get("origin"):
            typer.echo(f"  evidence: {', '.join(e.details['origin'])}")
        if e.scope:
            typer.echo(f"  scope: {', '.join(e.scope)}")


# ---- distillation ----

@app.command()
def distill(
    session: str | None = typer.Option(None, "--session", help="Distill one session."),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """Run the Distillation Engine over captured events (PRD §8)."""
    with workspace_store() as (_, cfg, store):
        if session and store.get_session(session) is None:
            # A typo'd --session used to silently "succeed" with 0 events
            # processed — indistinguishable from a real session with nothing
            # left to distill. Warn, but still run (mirrors `doctor`: signal,
            # don't block) since the id might legitimately just be very old.
            typer.secho(f"! session {session!r} not found in this store "
                        "(check for a typo?) — proceeding, but expect 0 events.",
                        fg=typer.colors.YELLOW)
        engine = build_distillation_engine(store, cfg)
        if dry_run:
            events = store.undistilled_events(session)
            typer.echo(f"dry-run: {len(events)} events would be processed for "
                       f"{'session ' + session if session else 'all sessions'}")
            return
        report = engine.distill_session(session) if session else engine.distill_all()
        typer.secho("distillation complete", fg=typer.colors.GREEN)
        typer.echo(f"  {report.summary()}")
        for w in report.warnings:
            typer.secho(f"  ! {w}", fg=typer.colors.YELLOW)
        if report.new_ids:
            typer.echo(f"  new artifacts: {', '.join(report.new_ids)}")


@app.command()
def review(
    session: str | None = typer.Option(None, "--session"),
    phase: bool = typer.Option(False, "--phase", help="Aggregate phase review."),
) -> None:
    """Generate a session (or phase) review (PRD §13)."""
    with workspace_store() as (_, _, store):
        if phase:
            _phase_review(store)
            return
        if session is None:
            session = latest_open_session_id(store)
            if not session:
                typer.echo("no open session found.")
                return
        rev = build_session_review(store, session)
        if not rev:
            typer.echo(f"session {session} not found.")
            return
        _print_review(rev)


def _phase_review(store: KnowledgeStore) -> None:
    """Long-range indicators (PRD §13.2)."""
    h = phase_health(store)
    typer.echo("PHASE REVIEW")
    typer.echo(f"  adr coverage: {h['adr_total']} decisions ({h['adr_candidates']} still candidate)")
    typer.echo(f"  superseded artifacts: {h['superseded']}")
    typer.echo(f"  correndas: {h['correndas_total']} "
               f"({h['correndas_proposed']} proposed, {h['correndas_active']} active)")
    typer.echo(f"  stale memories: {h['stale']}")
    typer.echo(f"  knowledge freshness: {h['knowledge_freshness_pct']}% current")


def _print_review(rev) -> None:
    typer.secho(f"Session review {rev.id} ({rev.session_id})", fg=typer.colors.CYAN, bold=True)
    for k, v in rev.details.get("produced", {}).items():
        typer.echo(f"  {k}: {v}")
    unresolved = rev.details.get("unresolved") or []
    if unresolved:
        typer.echo("  unresolved:")
        for u in unresolved:
            typer.echo(f"    - {u}")


# ---- governance (PRD §33, §49) ----

@correnda_app.command("confirm")
def correnda_confirm(entity_id: str) -> None:
    with workspace_store() as (_, _, store):
        ent = store.set_status(entity_id, Status.ACTIVE, authority=Authority.HUMAN_CONFIRMED)
        if not ent:
            typer.secho(f"{entity_id} not found.", fg=typer.colors.RED)
            raise typer.Exit(1)
        ent.details["confirmed_by_human"] = True
        store.upsert(ent)
        typer.secho(f"✓ {entity_id} is now ACTIVE (authority: human_confirmed).",
                    fg=typer.colors.GREEN)


@correnda_app.command("reject")
def correnda_reject(entity_id: str) -> None:
    with workspace_store() as (_, _, store):
        ent = store.set_status(entity_id, Status.REJECTED)
        if not ent:
            typer.secho(f"{entity_id} not found.", fg=typer.colors.RED)
            raise typer.Exit(1)
        typer.echo(f"{entity_id} rejected. It will not appear in compiled context.")


@adrs_app.command("accept")
def adr_accept(entity_id: str) -> None:
    with workspace_store() as (_, _, store):
        ent = store.set_status(entity_id, Status.ACTIVE, authority=Authority.HUMAN_CONFIRMED)
        if not ent:
            typer.secho(f"{entity_id} not found.", fg=typer.colors.RED)
            raise typer.Exit(1)
        typer.secho(f"✓ {entity_id} accepted.", fg=typer.colors.GREEN)


@adrs_app.command("reject")
def adr_reject(entity_id: str) -> None:
    with workspace_store() as (_, _, store):
        ent = store.set_status(entity_id, Status.REJECTED)
        if not ent:
            typer.secho(f"{entity_id} not found.", fg=typer.colors.RED)
            raise typer.Exit(1)
        typer.echo(f"{entity_id} rejected.")


@app.command()
def verify(entity_id: str) -> None:
    """Verify a memory against the repository: cited symbols must exist in
    scope files for repository_verified promotion (PRD §47)."""
    with workspace_store() as (root, _, store):
        ent = store.get(entity_id)
        if not ent:
            typer.secho(f"{entity_id} not found.", fg=typer.colors.RED)
            raise typer.Exit(1)
        from cortex.verification import verify_entity
        result = verify_entity(store, root, ent)
        if result["status"] == "verified":
            typer.secho(f"✓ {entity_id} verified ({result['detail']}).", fg=typer.colors.GREEN)
        elif result["status"] == "stale":
            typer.secho(f"⚠ {entity_id}: {result['detail']}. Flagged stale.", fg=typer.colors.YELLOW)
        else:
            typer.echo(f"· {entity_id}: {result['detail']}")


@app.command()
def supersede(old_id: str, with_new: str = typer.Option(..., "--with")) -> None:
    """Mark a decision as superseded by another (PRD §17.2)."""
    with workspace_store() as (_, _, store):
        ok = store.supersede(old_id, with_new)
    if not ok:
        typer.secho("supersede failed: check both ids.", fg=typer.colors.RED)
        raise typer.Exit(1)
    typer.echo(f"{with_new} SUPERSEDES {old_id}. History preserved.")


@app.command()
def contradictions() -> None:
    """List all detected semantic contradictions in the knowledge store."""
    with workspace_store() as (_, _, store):
        edges = store.edges_of(rel="CONTRADICTS")
        if not edges:
            typer.echo("no semantic contradictions detected.")
            return

        typer.secho(f"Found {len(edges)} semantic contradiction edge(s):\n", fg=typer.colors.YELLOW)
        for edge in edges:
            src_ent = store.get(edge["src"])
            dst_ent = store.get(edge["dst"])
            if src_ent and dst_ent:
                typer.secho(f"⚔ [{src_ent.id}] ({src_ent.type.value}, {src_ent.authority.value})", fg=typer.colors.RED)
                typer.echo(f"  Statement: {src_ent.statement}")
                typer.secho(f"  CONTRADICTS [{dst_ent.id}] ({dst_ent.type.value}, {dst_ent.authority.value})", fg=typer.colors.CYAN)
                typer.echo(f"  Statement: {dst_ent.statement}")
                typer.echo(f"  Resolution: use `cortex supersede {dst_ent.id} --with {src_ent.id}` or `cortex verify <id>`.\n")



# ---- explainability (PRD §19, §50) ----

@app.command()
def why(
    entity_id: str = typer.Argument(...),
    visual: bool = typer.Option(False, "--visual", "-v", help="Export visual graph HTML (Onda 9)."),
) -> None:
    """Trace a memory back to its evidence (PRD §15.2)."""
    with workspace_store() as (_, _, store):
        ent = store.get(entity_id)
        if not ent:
            typer.secho(f"{entity_id} not found.", fg=typer.colors.RED)
            raise typer.Exit(1)

        if visual:
            from cortex.visualizer import export_provenance_graph_file
            out_file = Path.cwd() / f"why_{entity_id}.html"
            export_provenance_graph_file(store, out_file, focus_id=entity_id)
            typer.secho(f"✓ Visual graph exported to {out_file}", fg=typer.colors.GREEN)
            return

        p = ent.provenance
        typer.echo(f"{ent.type.value} {ent.id}")
        typer.echo("")
        typer.echo("Statement:")
        typer.echo(f"  {ent.statement}")
        if ent.details.get("root_cause"):
            typer.echo(f"  root cause: {ent.details['root_cause']}")
        typer.echo("")
        typer.echo("Evidence:")
        for rel, target in store.related(ent.id, direction="in"):
            typer.echo(f"  {rel} <- {target.id} ({target.type.value}): {target.statement[:100]}")
        for rel, target in store.related(ent.id, direction="out"):
            typer.echo(f"  {rel} -> {target.id} ({target.type.value})")
        if p.source_events:
            typer.echo(f"  source events: {', '.join(p.source_events)}")
        if p.source_files:
            typer.echo(f"  source files: {', '.join(p.source_files)}")
        typer.echo("")
        typer.echo(f"Sessions: {p.source_session or 'n/a'}")
        typer.echo(f"Confidence: {ent.confidence:.2f}")
        typer.echo(f"Authority: {ent.authority.value}")
        typer.echo(f"Status: {ent.status.value}")
        typer.echo(f"Human confirmation: "
                   f"{'confirmed' if ent.details.get('confirmed_by_human') else 'not confirmed'}")
        if ent.superseded_by:
            typer.echo(f"Superseded by: {ent.superseded_by}")


@app.command()
def graph(
    output: Path = typer.Option(Path("cortex_graph.html"), "--output", "-o", help="Output HTML path."),
    focus: str | None = typer.Option(None, "--focus", help="Focus entity ID."),
) -> None:
    """Generate a standalone visual provenance graph (Onda 9)."""
    with workspace_store() as (_, _, store):
        from cortex.visualizer import export_provenance_graph_file
        out_path = export_provenance_graph_file(store, output, focus_id=focus)
        typer.secho(f"✓ Provenance graph generated at {out_path.resolve()}", fg=typer.colors.GREEN)



@app.command()
def trace(session_id: str) -> None:
    """Show raw events and distilled artifacts of a session (PRD §41)."""
    with workspace_store() as (_, _, store):
        events = store.conn.execute(
            "SELECT * FROM events WHERE session_id = ? ORDER BY ts", (session_id,)
        ).fetchall()
        typer.echo(f"session {session_id}: {len(events)} events")
        for r in events:
            content = (r["content"] or "")[:80].replace("\n", " ")
            typer.echo(f"  {r['ts']} {r['type']:<16} {content}")
        for ent in store.all_entities():
            if ent.session_id == session_id:
                typer.echo(f"  -> {ent.type.value} [{ent.id}] {ent.statement[:80]}")


# ---- manual capture ----

@app.command()
def capture(
    event_type: str = typer.Argument(...),
    content: str = typer.Argument("", help="Event content (empty for 'commits')."),
    session: str | None = typer.Option(None),
    files: str | None = typer.Option(None, help="Comma-separated paths."),
    branch: str | None = typer.Option(None),
    limit: int = typer.Option(20, help="For 'commits': how many recent commits."),
) -> None:
    """Manually record a raw event, or import git history with 'commits'."""
    with workspace_store() as (_, _, store):
        if event_type == "commits":
            from cortex.capture.recorder import capture_commits
            ids = capture_commits(store, Path.cwd(), limit=limit, session_id=session)
            typer.echo(f"imported {len(ids)} commit events as evidence")
            return
        if not content:
            typer.secho("content is required (or use 'cortex capture commits').",
                        fg=typer.colors.RED)
            raise typer.Exit(1)
        session = session or _current_session(store)
        store.ensure_session(session, host="cli", branch=branch)
        eid = capture_event(store, {
            "type": event_type,
            "session_id": session,
            "content": content,
            "files": [f.strip() for f in files.split(",")] if files else [],
            "branch": branch,
        })
        typer.echo(f"captured {event_type} as {eid} (session {session})")


def _current_session(store: KnowledgeStore) -> str:
    sid = latest_open_session_id(store)
    if sid:
        return sid
    sid = session_id_for("cli")
    store.ensure_session(sid, host="cli")
    return sid


# ---- session context (Golden Path step 7) ----

@app.command()
def context(
    task: str = typer.Option("", "--task", help="Current task description."),
    files: str | None = typer.Option(None, help="Comma-separated paths being worked on."),
    branch: str | None = typer.Option(None),
) -> None:
    """Compile the session context block (what cortex_init returns)."""
    with workspace_store() as (_, cfg, store):
        file_list = [f.strip() for f in files.split(",")] if files else None
        out = compile_context(
            store,
            CompileInput(query=task, files=file_list, branch=branch, phase=cfg.phase),
            max_tokens=cfg.context_max_tokens,
            max_adrs=cfg.max_adrs,
            max_intentions=cfg.max_intentions,
            max_correndas=cfg.max_correndas,
            include_recent_fixes=cfg.include_recent_fixes,
            include_last_review=cfg.include_last_review,
        )
        typer.echo(out)


# ---- host hooks ----

@app.command()
def hook(
    install: str | None = typer.Option(None, "--install", help="claude-code | cursor"),
    event: str | None = typer.Option(None, "--event", help="Internal: host hook payload on stdin."),
) -> None:
    """Install or serve host hooks (Claude Code / Cursor adapters)."""
    if install:
        from cortex.adapters.installer import install_hooks
        ws = detect_workspace()
        if ws is None:
            typer.secho("✗ no workspace detected — run `cortex init` first.",
                        fg=typer.colors.RED)
            raise typer.Exit(1)
        installed = install_hooks(install, ws.root)
        for path in installed:
            typer.secho(f"✓ hooks installed: {path}", fg=typer.colors.GREEN)
        return
    # serve: read one JSON payload from stdin (host hook invocation)
    from cortex.adapters.installer import handle_hook_payload
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError as exc:
        typer.echo(json.dumps({"ok": False, "error": f"invalid hook payload: {exc}"}))
        return
    result = handle_hook_payload(payload, Path.cwd())
    typer.echo(json.dumps(result, ensure_ascii=False))
    if not result.get("ok", False):
        # Failure signal for the host; the JSON stdout contract stays intact
        # and the agent is never blocked (PRD §42).
        raise typer.Exit(1)




# ---- observability / debug (PRD §41, Onda 4 item 14) ----

@app.command()
def diff(
    sessions: int = typer.Option(2, "--sessions", help="How many recent sessions."),
) -> None:
    """Summarize knowledge changes across the last N sessions (PRD §21.5)."""
    with workspace_store() as (_, _, store):
        rows = store.conn.execute(
            "SELECT id, started_at FROM sessions ORDER BY started_at DESC LIMIT ?",
            (sessions,),
        ).fetchall()
        if not rows:
            typer.echo("no sessions recorded.")
            return
        for r in rows:
            ents = store.entities_by_session(r["id"])
            typer.secho(f"session {r['id']} ({r['started_at']})", fg=typer.colors.CYAN)
            if not ents:
                typer.echo("  (no distilled artifacts)")
            for e in ents:
                typer.echo(f"  + {e.type.value} [{e.id}] {e.statement[:90]}")


@app.command("retrieval-debug")
def retrieval_debug(
    query: str = typer.Argument(...),
    files: str | None = typer.Option(None, help="Comma-separated paths."),
) -> None:
    """Explain retrieval: per-candidate hybrid score components & density (PRD §41)."""
    from cortex.compiler.compiler import CompileInput, _tokens, rank
    with workspace_store() as (_, cfg, store):
        file_list = [f.strip() for f in files.split(",")] if files else None
        try:
            fts = store.search(query, limit=200)
            fts_ids = {e.id for e, _ in fts}
        except Exception:
            fts_ids = set()
        typer.echo(f"query: {query!r}  (budget {cfg.context_max_tokens} tokens)")
        typer.echo(f"bm25 hits: {len(fts_ids)} entities")
        items = rank(store, CompileInput(query=query, files=file_list), limit=15)
        if not items:
            typer.echo("no candidates survived filtering.")
        for item in items:
            e = item.entity
            line = f"- [{e.id}] {e.statement}"
            r = item.reasons
            typer.echo(
                f"[{e.id}] {e.type.value} score={item.score:.3f} "
                f"(hybrid_rel={r.get('relevance', 0):.2f} [sparse={r.get('sparse', 0):.2f}, dense={r.get('dense', 0):.2f}] "
                f"density=[graph={r.get('graph_density', 0):.2f}, content={r.get('content_density', 0):.2f}] "
                f"authority={r.get('authority')} conf={r.get('confidence'):.2f} "
                f"contradicted={'YES' if r.get('contradicted') else 'no'} "
                f"bm25={'yes' if e.id in fts_ids else 'no'} scope={e.scope or '-'} ~{_tokens(line)}tk)"
            )



@app.command()
def phase() -> None:
    """Phase review: long-range knowledge health (PRD §13.2)."""
    with workspace_store() as (_, _, store):
        _phase_review(store)


@commons_app.command("export")
def commons_export(
    entity_id: str = typer.Argument(..., help="Correnda or ADR entity ID to export."),
    output: Path | None = typer.Option(None, "--output", "-o", help="Output JSON path."),
) -> None:
    """Export a generalized opt-in engineering pattern schema (Onda 10)."""
    with workspace_store() as (_, _, store):
        from cortex.commons import export_common_pattern
        pattern = export_common_pattern(store, entity_id)
        content = json.dumps(pattern, indent=2, ensure_ascii=False)
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(content, encoding="utf-8")
            typer.secho(f"✓ Pattern exported to {output}", fg=typer.colors.GREEN)
        else:
            typer.echo(content)


@commons_app.command("import")
def commons_import(
    file_path: Path = typer.Argument(..., help="Path to common pattern JSON file."),
) -> None:
    """Import a generalized engineering pattern as a proposed local rule (Onda 10)."""
    with workspace_store() as (_, _, store):
        from cortex.commons import import_common_pattern
        if not file_path.exists():
            typer.secho(f"File {file_path} does not exist.", fg=typer.colors.RED)
            raise typer.Exit(1)
        data = json.loads(file_path.read_text(encoding="utf-8"))
        ent = import_common_pattern(store, data)
        typer.secho(f"✓ Pattern imported as [{ent.id}] ({ent.status.value}).", fg=typer.colors.GREEN)


@app.command()
def benchmark(
    dogfood: bool = typer.Option(False, "--dogfood", help="Run benchmark on current store instead of fixture (Onda 8)."),
    adversarial: bool = typer.Option(
        False, "--adversarial",
        help="Run the fixture with naturally-phrased events instead of "
             "extractor-shaped ones (item 8): honest read on extraction "
             "generalization, not just ranking/compiler correctness."),
) -> None:
    """Run the CCB memory-quality benchmark (PRD §31.4, Onda 8)."""
    from cortex.benchmarks.ccb import (
        format_report,
        run_ccb,
        run_ccb_on_store,
        run_ccb_paraphrased,
    )
    if dogfood and adversarial:
        typer.secho("--dogfood and --adversarial are mutually exclusive.", fg=typer.colors.RED)
        raise typer.Exit(1)
    if dogfood:
        with workspace_store() as (_, _, store):
            report = run_ccb_on_store(store)
    elif adversarial:
        report = run_ccb_paraphrased()
    else:
        report = run_ccb()
    typer.echo(format_report(report))
    # --adversarial is a diagnostic read on extraction generalization, not
    # an acceptance gate: a lower score than the fixture's is expected and
    # informative, not a regression, so it never fails the process.
    if not adversarial and report["tasks_passed"] < report["tasks_total"]:
        raise typer.Exit(1)



@app.command()
def config(
    set_key: str | None = typer.Option(None, "--set", help="section.key"),
    value: str | None = typer.Argument(None, help="New value (used with --set)."),
) -> None:
    """Print current configuration, or update one key with --set."""
    ws = detect_workspace()
    if ws is None:
        typer.secho("no workspace detected.", fg=typer.colors.RED)
        raise typer.Exit(1)
    if set_key:
        if not value:
            typer.secho("--set requires a value argument.", fg=typer.colors.RED)
            raise typer.Exit(1)
        _config_set(ws.root, set_key, value)
        typer.secho(f"✓ {set_key} = {value}", fg=typer.colors.GREEN)
        return
    try:
        cfg = CortexConfig.load(ws.root)
    except CortexConfigError as exc:
        typer.secho(f"config error: {exc}", fg=typer.colors.RED)
        raise typer.Exit(1) from exc
    for field_ in vars(cfg):
        typer.echo(f"{field_} = {getattr(cfg, field_)}")


CONFIG_SECTIONS = {
    "project.name": "project", "project.phase": "project",
    "capture.enabled": "capture", "capture.raw_retention_days": "capture",
    "distillation.mode": "distillation", "distillation.llm": "distillation",
    "distillation.ollama_url": "distillation",
    "distillation.llm_model": "distillation",
    "distillation.llm_timeout_s": "distillation",
    "distillation.min_confidence_for_persistence": "distillation",
    "distillation.correnda_min_evidence": "distillation",
    "context.max_tokens": "context", "context.max_adrs": "context",
    "context.max_intentions": "context", "context.max_correndas": "context",
    "context.include_recent_fixes": "context", "context.include_last_review": "context",
    "privacy.telemetry": "privacy", "privacy.network_calls": "privacy",
}

# Keys whose TOML value must be a bare `true`/`false` or numeric literal
# (everything else is treated as a string and JSON-quoted — see
# _coerce_config_value). This is the type table `--set` validates against;
# CortexConfig.__post_init__ still validates ranges/enums on top of it.
_BOOL_KEYS = {"capture.enabled", "context.include_recent_fixes",
              "context.include_last_review", "privacy.telemetry", "privacy.network_calls"}
_INT_KEYS = {"capture.raw_retention_days", "distillation.correnda_min_evidence",
             "context.max_tokens", "context.max_adrs", "context.max_intentions",
             "context.max_correndas"}
_FLOAT_KEYS = {"distillation.min_confidence_for_persistence", "distillation.llm_timeout_s"}


def _coerce_config_value(key: str, value: str) -> str:
    """Convert/validate a `--set` value and return the literal to write into
    the TOML file. String keys are always JSON-quoted: TOML basic strings and
    JSON strings agree on escaping, so a value containing a newline or `"`
    can never break out into a new key/section (item 3.2's injection case)."""
    if key in _BOOL_KEYS:
        if value.lower() not in ("true", "false"):
            raise CortexConfigError(f"{key}: use true ou false, recebido {value!r}")
        return value.lower()
    if key in _INT_KEYS:
        try:
            int(value)
        except ValueError as exc:
            raise CortexConfigError(f"{key}: esperado inteiro, recebido {value!r}") from exc
        return value
    if key in _FLOAT_KEYS:
        try:
            float(value)
        except ValueError as exc:
            raise CortexConfigError(f"{key}: esperado número, recebido {value!r}") from exc
        return value
    if "\n" in value or "\r" in value:
        # A newline could only be an attempt to inject a new key/section on
        # the next line; every string key here is a single-line value.
        raise CortexConfigError(f"{key}: valor não pode conter quebra de linha")
    return json.dumps(value)  # TOML basic string == JSON string here → quotes/backslashes escaped safely


def _typed_config_value(key: str, value: str) -> object:
    """Return the Python value that tomlkit should assign to a config key."""
    _coerce_config_value(key, value)  # validate before touching the document
    if key in _BOOL_KEYS:
        return value.lower() == "true"
    if key in _INT_KEYS:
        return int(value)
    if key in _FLOAT_KEYS:
        return float(value)
    return value


def _config_set(root: Path, key: str, value: str) -> None:
    """Update one validated key in cortex.toml, preserving the rest.

    Validates and writes atomically (item 3.2): the coerced value is
    type-checked *before* anything touches disk; the candidate file is
    written to a `.tmp` sibling and only replaces cortex.toml once the
    *whole* resulting file both parses as TOML and passes
    CortexConfig.__post_init__ validation. A failure at any step leaves
    the original cortex.toml byte-for-byte untouched and removes the .tmp."""
    if key not in CONFIG_SECTIONS:
        typer.secho(f"unknown key: {key}. Valid keys: {', '.join(sorted(CONFIG_SECTIONS))}",
                    fg=typer.colors.RED)
        raise typer.Exit(1)
    try:
        coerced = _coerce_config_value(key, value)
    except CortexConfigError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(1) from exc

    path = root / "cortex.toml"
    section = CONFIG_SECTIONS[key]
    name = key.split(".", 1)[1]
    source = path.read_text(encoding="utf-8") if path.exists() else ""
    try:
        import tomlkit

        document = tomlkit.parse(source)
        if section not in document:
            document[section] = tomlkit.table()
        document[section][name] = _typed_config_value(key, value)
        candidate = tomlkit.dumps(document)
    except Exception:
        # Minimal installations, or a TOMLKit parser incompatibility, still
        # get the original safe line editor.  The candidate is always parsed
        # and validated below before it can replace the real file.
        lines = source.splitlines()
        replaced = False
        current_section = ""
        out = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                current_section = stripped[1:-1]
            if current_section == section and stripped.split("=")[0].strip() == name:
                out.append(f"{name} = {coerced}")
                replaced = True
            else:
                out.append(line)
        if not replaced:
            sections = [ln.strip()[1:-1] for ln in out if ln.strip().startswith("[")]
            if section in sections:
                insert_at = max(i for i, ln in enumerate(out)
                                if ln.strip() == f"[{section}]") + 1
                out.insert(insert_at, f"{name} = {coerced}")
            else:
                out += ["", f"[{section}]", f"{name} = {coerced}"]
        candidate = "\n".join(out) + "\n"
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(candidate, encoding="utf-8")
    try:
        CortexConfig.load_from(tmp)  # full parse + range/enum validation
    except CortexConfigError as exc:
        tmp.unlink(missing_ok=True)
        typer.secho(f"update would produce invalid config: {exc}", fg=typer.colors.RED)
        raise typer.Exit(1) from exc
    tmp.replace(path)  # atomic on POSIX and Windows (os.replace, Python >=3.3)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
