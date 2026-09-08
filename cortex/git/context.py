"""Git context (branch, recent commits) used by capture and distillation."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GitContext:
    available: bool = False
    branch: str | None = None
    recent_commits: list[dict[str, str]] = field(default_factory=list)
    dirty: bool = False


def _git(root: Path, *args: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True, text=True, timeout=10, check=True,
            shell=False,
        )
        return out.stdout.strip()
    except Exception:
        return None


def git_context(root: Path) -> GitContext:
    ctx = GitContext()
    if not (root / ".git").exists():
        return ctx
    branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD")
    if branch is None:
        return ctx
    ctx.available = True
    ctx.branch = branch
    log = _git(root, "log", "-5", "--pretty=%H%x00%s%x00%an")
    if log:
        for line in log.splitlines():
            parts = line.split("\x00")
            if len(parts) == 3:
                ctx.recent_commits.append({"hash": parts[0][:7], "message": parts[1], "author": parts[2]})
    status = _git(root, "status", "--porcelain")
    ctx.dirty = bool(status)
    return ctx
