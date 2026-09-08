"""Shared fixtures: temporary git workspace with Cortex initialized."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from cortex.config import write_default_config
from cortex.storage.store import KnowledgeStore
from cortex.workspace import CORTEX_DIR, ensure_cortex_dir


@pytest.fixture
def project(tmp_path: Path) -> Path:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "handlers").mkdir()
    (tmp_path / "src" / "handlers" / "webhook_handler.py").write_text("def handle(): ...\n")
    (tmp_path / "src" / "db").mkdir()
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.email", "t@t.t"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "t"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-qm", "initial"], check=True)
    write_default_config(tmp_path, "test-project")
    ensure_cortex_dir(tmp_path)
    return tmp_path


@pytest.fixture
def store(project: Path) -> KnowledgeStore:
    s = KnowledgeStore(project / CORTEX_DIR / "cortex.db")
    yield s
    s.close()
