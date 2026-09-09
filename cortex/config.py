"""Configuration loading (cortex.toml) with PRD defaults."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CONFIG_TEMPLATE = """\
# Cortex configuration
# Docs: local-first, provenance-first, engineering-first

[project]
name = "{project_name}"
phase = "develop"

[workspace]
strategy = "git"

[capture]
enabled = true
raw_retention_days = 30

[distillation]
mode = "offline"
llm = "heuristic"            # heuristic | auto | ollama
ollama_url = "http://localhost:11434"
llm_model = "qwen2.5:7b"
llm_timeout_s = 30.0         # capped to 10s inside the Stop hook
min_confidence_for_persistence = 0.60
correnda_min_evidence = 2

[context]
max_tokens = 2000
max_adrs = 5
max_intentions = 5
max_correndas = 7
include_recent_fixes = true
include_last_review = true

[privacy]
telemetry = false
network_calls = false        # local-only by default

[multi_agent]
enabled = false
conflict_strategy = "append-and-resolve"
"""


@dataclass
class CortexConfig:
    project_name: str = "untitled"
    phase: str = "develop"
    capture_enabled: bool = True
    raw_retention_days: int = 30
    distill_mode: str = "offline"
    llm: str = "heuristic"
    ollama_url: str = "http://localhost:11434"
    llm_model: str = "qwen2.5:7b"
    llm_timeout_s: float = 30.0
    min_confidence_for_persistence: float = 0.60
    correnda_min_evidence: int = 2
    context_max_tokens: int = 2000
    max_adrs: int = 5
    max_intentions: int = 5
    max_correndas: int = 7
    include_recent_fixes: bool = True
    include_last_review: bool = True
    telemetry: bool = False
    network_calls: bool = False
    multi_agent: bool = False
    federation_stores: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, root: Path) -> CortexConfig:
        path = root / "cortex.toml"
        cfg = cls()
        if path.exists():
            data = tomllib.loads(path.read_text(encoding="utf-8"))
            proj = data.get("project", {})
            cfg.project_name = proj.get("name", cfg.project_name)
            cfg.phase = proj.get("phase", cfg.phase)
            cap = data.get("capture", {})
            cfg.capture_enabled = bool(cap.get("enabled", cfg.capture_enabled))
            cfg.raw_retention_days = int(cap.get("raw_retention_days", cfg.raw_retention_days))
            dis = data.get("distillation", {})
            cfg.distill_mode = dis.get("mode", cfg.distill_mode)
            cfg.llm = dis.get("llm", cfg.llm)
            cfg.ollama_url = dis.get("ollama_url", cfg.ollama_url)
            cfg.llm_model = dis.get("llm_model", cfg.llm_model)
            cfg.llm_timeout_s = float(dis.get("llm_timeout_s", cfg.llm_timeout_s))
            cfg.min_confidence_for_persistence = float(
                dis.get("min_confidence_for_persistence", cfg.min_confidence_for_persistence)
            )
            cfg.correnda_min_evidence = int(dis.get("correnda_min_evidence", cfg.correnda_min_evidence))
            ctx = data.get("context", {})
            cfg.context_max_tokens = int(ctx.get("max_tokens", cfg.context_max_tokens))
            cfg.max_adrs = int(ctx.get("max_adrs", cfg.max_adrs))
            cfg.max_intentions = int(ctx.get("max_intentions", cfg.max_intentions))
            cfg.max_correndas = int(ctx.get("max_correndas", cfg.max_correndas))
            cfg.include_recent_fixes = bool(ctx.get("include_recent_fixes", cfg.include_recent_fixes))
            cfg.include_last_review = bool(ctx.get("include_last_review", cfg.include_last_review))
            priv = data.get("privacy", {})
            cfg.telemetry = bool(priv.get("telemetry", cfg.telemetry))
            cfg.network_calls = bool(priv.get("network_calls", cfg.network_calls))
            fed = data.get("federation", {})
            cfg.federation_stores = fed.get("stores", cfg.federation_stores)
        return cfg

    def to_toml(self) -> str:
        return DEFAULT_CONFIG_TEMPLATE.format(project_name=self.project_name)


def write_default_config(root: Path, project_name: str) -> Path:
    path = root / "cortex.toml"
    path.write_text(DEFAULT_CONFIG_TEMPLATE.format(project_name=project_name), encoding="utf-8")
    return path
