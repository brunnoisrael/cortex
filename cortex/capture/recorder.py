"""Raw session capture (PRD §7): temporary evidence layer, redacted before storage."""

from __future__ import annotations

from typing import Any

from cortex.privacy.redaction import redact
from cortex.storage.store import KnowledgeStore

EVENT_TYPES = (
    "session_start", "session_end", "agent_response", "agent_thought",
    "tool_call", "tool_result", "file_read", "file_edit", "commit",
    "pre_compact", "user_instruction", "error", "test_failure", "test_success",
)


def capture_event(store: KnowledgeStore, event: dict[str, Any]) -> str:
    """Persist one raw event after redaction. Never raises to the caller's session."""
    content = redact(event.get("content"))
    files = [redact(f) for f in (event.get("files") or [])]
    return store.add_event({**event, "content": content, "files": files})


def session_event(store: KnowledgeStore, host: str, session_id: str, kind: str,
                  branch: str | None = None) -> None:
    store.ensure_session(session_id, host, branch=branch)
    capture_event(store, {
        "type": kind,
        "session_id": session_id,
        "branch": branch,
    })


def capture_commits(store: KnowledgeStore, root, limit: int = 20,
                    session_id: str | None = None) -> list[str]:
    """Import recent commit messages as `commit` events — git is evidence
    (PRD §8.3, Onda 3 item 8)."""
    from cortex.git.context import _git
    log = _git(root, "log", f"-{limit}", "--pretty=%H%x00%s%x00%b")
    if not log:
        return []
    ids = []
    sid = session_id or "sess-git-import"
    store.ensure_session(sid, host="git")
    for line in log.splitlines():
        parts = line.split("\x00")
        if len(parts) < 2 or not parts[1].strip():
            continue
        message = (parts[1] + " " + (parts[2] if len(parts) > 2 else "")).strip()
        ids.append(capture_event(store, {
            "type": "commit",
            "session_id": sid,
            "content": message[:500],
            "branch": None,
            "meta": {"hash": parts[0]},
        }))
    return ids
