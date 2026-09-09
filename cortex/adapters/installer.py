"""Host adapters (PRD §6): MCP exposes knowledge; hooks capture sessions.

Adapter contract — each adapter declares its capabilities (PRD §6.2).
Onda 1: the `Stop` hook now triggers offline distillation automatically
(Golden Path §54 step 5) plus raw-event retention purge (§7.2) — always
async-safe for the host: any failure degrades to {"ok": false} (PRD §42).
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

ADAPTER_CAPABILITIES = {
    "claude-code": {
        "id": "claude_code",
        "capabilities": {
            "session_start": True, "session_end": True, "agent_response": True,
            "agent_thought": False, "pre_compact": True, "tool_use": True,
            "file_events": True, "branch_context": True,
        },
        "hook_events": ["SessionStart", "UserPromptSubmit", "PostToolUse", "Stop", "PreCompact"],
    },
    "cursor": {
        "id": "cursor",
        "capabilities": {
            "session_start": True, "session_end": True, "agent_response": True,
            "agent_thought": False, "pre_compact": False, "tool_use": True,
            "file_events": True, "branch_context": True,
        },
        "hook_events": ["beforeSubmitPrompt", "afterFileEdit", "stop"],
    },
}

CLAUDE_HOOK_SCRIPT = "cortex hook --event claude-code"
CURSOR_HOOK_SCRIPT = "cortex hook --event cursor"

CLAUDE_SETTINGS_SNIPPET = {
    "hooks": {
        "SessionStart": [{"hooks": [{"type": "command", "command": CLAUDE_HOOK_SCRIPT}]}],
        "UserPromptSubmit": [{"hooks": [{"type": "command", "command": CLAUDE_HOOK_SCRIPT}]}],
        "PostToolUse": [{"hooks": [{"type": "command", "command": CLAUDE_HOOK_SCRIPT}]}],
        "Stop": [{"hooks": [{"type": "command", "command": CLAUDE_HOOK_SCRIPT}]}],
    }
}

CURSOR_HOOKS_SNIPPET = {
    "version": 1,
    "hooks": {
        "beforeSubmitPrompt": [{"command": CURSOR_HOOK_SCRIPT}],
        "stop": [{"command": CURSOR_HOOK_SCRIPT}],
    },
}

# Onda 6: Instruction prompt snippet for agents to natively invoke cortex_emit
CORTEX_EMIT_INSTRUCTION = """
[CORTEX DIRECTIVE]
When making architectural decisions (ADRs), rejecting alternative approaches, discovering critical bug fixes, or identifying anti-patterns (negative knowledge), invoke the MCP tool `cortex_emit` with structured details (kind, statement, rationale, alternatives_rejected, scope).
"""

# Cursor gives no session id: a new session = gap > IDLE_TIMEOUT since the
# last prompt in the same workspace (Onda 4, item 13).
IDLE_TIMEOUT_SECONDS = 30 * 60



def _merge_json(path: Path, snippet: dict) -> Path:
    data: dict[str, Any] = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    for key, value in snippet.items():
        if isinstance(value, dict) and isinstance(data.get(key), dict):
            data[key] = {**data[key], **value}
        else:
            data[key] = value
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def install_hooks(host: str, root: Path) -> list[Path]:
    host = host.lower()
    if host in ("claude-code", "claude_code", "claudecode"):
        return [_merge_json(root / ".claude" / "settings.json", CLAUDE_SETTINGS_SNIPPET)]
    if host == "cursor":
        return [_merge_json(root / ".cursor" / "hooks.json", CURSOR_HOOKS_SNIPPET)]
    raise ValueError(f"unknown host: {host}")


def _cursor_session_id(cortex_dir: Path) -> str:
    """Stable session id across a Cursor session, new id after an idle gap."""
    state_path = cortex_dir / "cursor_session.json"
    now = time.time()
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            if now - state.get("last_seen", 0) < IDLE_TIMEOUT_SECONDS:
                state["last_seen"] = now
                state_path.write_text(json.dumps(state), encoding="utf-8")
                return state["session_id"]
        except (json.JSONDecodeError, OSError):
            pass
    sid = f"sess-cursor-{uuid.uuid4().hex[:8]}"
    cortex_dir.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps({"session_id": sid, "last_seen": now}), encoding="utf-8")
    return sid


def _auto_distill(ws, cfg, session_id: str) -> str | None:
    """Offline distillation at session end (PRD §8.2, §42: best-effort)."""
    try:
        from cortex.distillation.engine import DistillationEngine
        from cortex.distillation.review import build_session_review
        from cortex.storage.store import KnowledgeStore
        store = KnowledgeStore(ws.db_path)
        try:
            engine = DistillationEngine(
                store,
                min_confidence=cfg.min_confidence_for_persistence,
                correnda_min_evidence=cfg.correnda_min_evidence,
                retention_days=cfg.raw_retention_days,
                llm=cfg.llm,
                ollama_url=getattr(cfg, "ollama_url", None),
                llm_model=getattr(cfg, "llm_model", None),
                # The Stop hook runs at the end of every user session: the LLM
                # pass gets a capped timeout so a dead server can't hold it.
                llm_timeout_s=min(float(getattr(cfg, "llm_timeout_s", 30.0)), 10.0),
            )
            report = engine.distill_session(session_id)
            build_session_review(store, session_id)
            return report.summary()
        finally:
            store.close()
    except Exception:
        return None  # never block the host session


def handle_hook_payload(payload: dict[str, Any], root: Path) -> dict[str, Any]:
    """Normalize a host hook payload into a Cortex raw event. Failures must
    never block the host session (PRD §42) — errors are returned, not raised."""
    try:
        from cortex.capture.recorder import capture_event
        from cortex.config import CortexConfig
        from cortex.storage.store import KnowledgeStore
        from cortex.workspace import detect_workspace, ensure_cortex_dir

        ws = detect_workspace(root)
        if ws is None:
            return {"ok": False, "error": "workspace not detected"}
        if not ws.db_path.exists():
            ensure_cortex_dir(ws)
        cfg = CortexConfig.load(ws.root)
        if not cfg.capture_enabled:
            return {"ok": True, "skipped": "capture disabled"}

        host = payload.get("_host") or "claude-code"
        hook_name = payload.get("hook_event_name") or payload.get("hook_name") or ""
        etype = CLAUDE_EVENT_MAP.get(hook_name) or CURSOR_EVENT_MAP.get(hook_name)
        if etype is None:
            etype = CURSOR_EVENT_MAP.get(payload.get("event") or "", "tool_result")

        content = (
            payload.get("prompt")
            or payload.get("message")
            or json.dumps(payload.get("tool_input") or "", ensure_ascii=False)
            or None
        )
        if hook_name == "PostToolUse":
            tool_input = payload.get("tool_input") or {}
            content = json.dumps(tool_input, ensure_ascii=False)[:2000]
        files = []
        if isinstance(payload.get("tool_input"), dict):
            fp = payload["tool_input"].get("file_path")
            if fp:
                files = [fp]

        session_id = payload.get("session_id")
        if not session_id:
            if host.startswith("cursor"):
                session_id = _cursor_session_id(ws.cortex_dir)
            else:
                session_id = f"sess-{host[:4].lower()}-{uuid.uuid4().hex[:6]}"

        store = KnowledgeStore(ws.db_path)
        try:
            store.ensure_session(session_id, host=host, branch=payload.get("branch"))
            eid = capture_event(store, {
                "type": etype,
                "session_id": session_id,
                "content": content,
                "files": files,
                "branch": payload.get("branch"),
                "meta": {"hook": hook_name, "host": host},
            })
        finally:
            store.close()

        response: dict[str, Any] = {"ok": True, "event": eid, "session": session_id}
        if etype == "session_start":
            from cortex.compiler.compiler import CompileInput, compile_context
            store = KnowledgeStore(ws.db_path)
            try:
                ctx = compile_context(store, CompileInput(branch=payload.get("branch")),
                                      max_tokens=cfg.context_max_tokens)
            finally:
                store.close()
            response["context"] = ctx
        if etype == "session_end" and cfg.distill_mode in ("offline", "both"):
            summary = _auto_distill(ws, cfg, session_id)
            if summary:
                response["distilled"] = summary
        return response
    except Exception as exc:  # PRD §42: memory failure must not block the agent
        return {"ok": False, "error": str(exc), "minimal_safe_context": True}


CLAUDE_EVENT_MAP = {
    "SessionStart": "session_start",
    "UserPromptSubmit": "user_instruction",
    "PostToolUse": "tool_result",
    "Stop": "session_end",
    "PreCompact": "pre_compact",
}
CURSOR_EVENT_MAP = {
    "beforeSubmitPrompt": "user_instruction",
    "afterFileEdit": "file_edit",
    "stop": "session_end",
}
