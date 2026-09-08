"""Workspace detection (PRD §22) and Cortex home layout (PRD §35 storage)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

WORKSPACE_MARKERS = [
    ("cortex.toml", 1),
    (".git", 2),
    ("package.json", 3),
    ("pyproject.toml", 4),
    ("Cargo.toml", 5),
    ("go.mod", 6),
    ("pom.xml", 7),
]

CORTEX_DIR = ".cortex"
STORE_FILE = "cortex.db"
SESSIONS_FILE = "sessions.jsonl"


@dataclass
class Workspace:
    root: Path
    strategy: str  # which marker identified the root

    @property
    def cortex_dir(self) -> Path:
        return self.root / CORTEX_DIR

    @property
    def db_path(self) -> Path:
        return self.cortex_dir / STORE_FILE

    @property
    def events_path(self) -> Path:
        return self.cortex_dir / SESSIONS_FILE

    @property
    def project_id(self) -> str:
        """Stable identity derived from the absolute root path, not folder name."""
        import hashlib
        return hashlib.sha256(str(self.root.resolve()).encode()).hexdigest()[:16]


def detect_workspace(start: Path | None = None) -> Workspace | None:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        for marker, priority in sorted(WORKSPACE_MARKERS, key=lambda m: m[1]):
            if (candidate / marker).exists():
                if marker == "cortex.toml" or (candidate / ".cortex").exists():
                    return Workspace(root=candidate, strategy="cortex")
                return Workspace(root=candidate, strategy=marker)
        # git root wins even without other markers
        if (candidate / ".git").exists():
            return Workspace(root=candidate, strategy="git")
    return None


def ensure_cortex_dir(ws: Workspace | Path) -> Path:
    if isinstance(ws, Path):
        target = ws / CORTEX_DIR
    else:
        target = ws.cortex_dir
    target.mkdir(parents=True, exist_ok=True)
    return target
