"""Configuration loading (cortex.toml) with PRD defaults."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


class CortexConfigError(Exception):
    """A cortex.toml value could not be parsed or fails validation.

    Raised instead of letting TOMLDecodeError/ValueError/TypeError escape
    raw: every CLI command and every MCP tool loads config on the hot path,
    so a config error must produce a one-line, actionable message rather
    than a traceback (PLANO_ENDURECIMENTO_2026-09-08.md item 3.1)."""


_ALLOWED_LLM = {"heuristic", "auto", "ollama"}
_ALLOWED_DISTILL_MODES = {"offline", "online", "both"}


def _as_bool(section: str, key: str, value: object, default: bool) -> bool:
    """Strict boolean coercion: TOML `true`/`false` only.

    bool("false") == True in plain Python, so a quoted string in the config
    file must be rejected rather than silently coerced to True."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    raise CortexConfigError(
        f"cortex.toml [{section}] {key}: esperado booleano (true/false), recebido {value!r}"
    )


def _as_int(section: str, key: str, value: object, default: int,
            minimum: int | None = None) -> int:
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, (int, float)) or int(value) != value:
        raise CortexConfigError(
            f"cortex.toml [{section}] {key}: esperado inteiro, recebido {value!r}"
        )
    n = int(value)
    if minimum is not None and n < minimum:
        raise CortexConfigError(
            f"cortex.toml [{section}] {key}: mínimo {minimum}, recebido {n}"
        )
    return n


def _as_float(section: str, key: str, value: object, default: float,
              minimum: float | None = None, maximum: float | None = None) -> float:
    if value is None:
        return default
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CortexConfigError(
            f"cortex.toml [{section}] {key}: esperado número, recebido {value!r}"
        )
    n = float(value)
    if minimum is not None and n < minimum:
        raise CortexConfigError(
            f"cortex.toml [{section}] {key}: mínimo {minimum}, recebido {n}"
        )
    if maximum is not None and n > maximum:
        raise CortexConfigError(
            f"cortex.toml [{section}] {key}: máximo {maximum}, recebido {n}"
        )
    return n


def _as_str(section: str, key: str, value: object, default: str,
            allowed: set[str] | None = None) -> str:
    if value is None:
        return default
    if not isinstance(value, str):
        raise CortexConfigError(
            f"cortex.toml [{section}] {key}: esperado texto, recebido {value!r}"
        )
    if allowed is not None and value not in allowed:
        raise CortexConfigError(
            f"cortex.toml [{section}] {key}={value!r} inválido; use {' | '.join(sorted(allowed))}"
        )
    return value


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
network_calls = false        # local-only by default: non-loopback ollama_url
                              # is refused unless this is true (PLANO item 3.4)
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

    def __post_init__(self) -> None:
        """Range/enum validation (item 3.1): defaults above are always valid,
        so this only ever fires for values that came from a user's
        cortex.toml via load()."""
        if not 0.0 <= self.min_confidence_for_persistence <= 1.0:
            raise CortexConfigError(
                "distillation.min_confidence_for_persistence deve estar em [0,1]: "
                f"{self.min_confidence_for_persistence}"
            )
        if self.context_max_tokens < 100:
            raise CortexConfigError(
                f"context.max_tokens mínimo é 100: {self.context_max_tokens}"
            )
        if self.raw_retention_days < 0:
            raise CortexConfigError(
                f"capture.raw_retention_days não pode ser negativo: {self.raw_retention_days}"
            )
        if self.correnda_min_evidence < 1:
            raise CortexConfigError(
                f"distillation.correnda_min_evidence mínimo é 1: {self.correnda_min_evidence}"
            )
        if self.llm_timeout_s <= 0:
            raise CortexConfigError(
                f"distillation.llm_timeout_s deve ser positivo: {self.llm_timeout_s}"
            )
        if self.llm not in _ALLOWED_LLM:
            raise CortexConfigError(
                f"distillation.llm={self.llm!r} inválido; use {' | '.join(sorted(_ALLOWED_LLM))}"
            )
        if self.distill_mode not in _ALLOWED_DISTILL_MODES:
            raise CortexConfigError(
                f"distillation.mode={self.distill_mode!r} inválido; "
                f"use {' | '.join(sorted(_ALLOWED_DISTILL_MODES))}"
            )

    @classmethod
    def load(cls, root: Path) -> CortexConfig:
        path = root / "cortex.toml"
        if not path.exists():
            return cls()
        return cls.load_from(path)

    @classmethod
    def load_from(cls, path: Path) -> CortexConfig:
        """Parse and validate a cortex.toml at an exact path (item 3.2 uses
        this to validate a candidate file before it replaces the real one)."""
        try:
            data = tomllib.loads(path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as exc:
            raise CortexConfigError(f"cortex.toml não pôde ser interpretado: {exc}") from exc

        defaults = cls()
        proj = data.get("project", {})
        cap = data.get("capture", {})
        dis = data.get("distillation", {})
        ctx = data.get("context", {})
        priv = data.get("privacy", {})

        return cls(
            project_name=_as_str("project", "name", proj.get("name"), defaults.project_name),
            phase=_as_str("project", "phase", proj.get("phase"), defaults.phase),
            capture_enabled=_as_bool("capture", "enabled", cap.get("enabled"),
                                     defaults.capture_enabled),
            raw_retention_days=_as_int("capture", "raw_retention_days",
                                        cap.get("raw_retention_days"),
                                        defaults.raw_retention_days),
            distill_mode=_as_str("distillation", "mode", dis.get("mode"),
                                  defaults.distill_mode),
            llm=_as_str("distillation", "llm", dis.get("llm"), defaults.llm),
            ollama_url=_as_str("distillation", "ollama_url", dis.get("ollama_url"),
                                defaults.ollama_url),
            llm_model=_as_str("distillation", "llm_model", dis.get("llm_model"),
                               defaults.llm_model),
            llm_timeout_s=_as_float("distillation", "llm_timeout_s",
                                     dis.get("llm_timeout_s"), defaults.llm_timeout_s),
            min_confidence_for_persistence=_as_float(
                "distillation", "min_confidence_for_persistence",
                dis.get("min_confidence_for_persistence"),
                defaults.min_confidence_for_persistence,
            ),
            correnda_min_evidence=_as_int(
                "distillation", "correnda_min_evidence", dis.get("correnda_min_evidence"),
                defaults.correnda_min_evidence,
            ),
            context_max_tokens=_as_int("context", "max_tokens", ctx.get("max_tokens"),
                                        defaults.context_max_tokens),
            max_adrs=_as_int("context", "max_adrs", ctx.get("max_adrs"),
                              defaults.max_adrs, minimum=0),
            max_intentions=_as_int("context", "max_intentions", ctx.get("max_intentions"),
                                    defaults.max_intentions, minimum=0),
            max_correndas=_as_int("context", "max_correndas", ctx.get("max_correndas"),
                                   defaults.max_correndas, minimum=0),
            include_recent_fixes=_as_bool("context", "include_recent_fixes",
                                           ctx.get("include_recent_fixes"),
                                           defaults.include_recent_fixes),
            include_last_review=_as_bool("context", "include_last_review",
                                          ctx.get("include_last_review"),
                                          defaults.include_last_review),
            telemetry=_as_bool("privacy", "telemetry", priv.get("telemetry"),
                                defaults.telemetry),
            network_calls=_as_bool("privacy", "network_calls", priv.get("network_calls"),
                                    defaults.network_calls),
        )

    def to_toml(self) -> str:
        return DEFAULT_CONFIG_TEMPLATE.format(project_name=self.project_name)


def write_default_config(root: Path, project_name: str) -> Path:
    path = root / "cortex.toml"
    path.write_text(DEFAULT_CONFIG_TEMPLATE.format(project_name=project_name), encoding="utf-8")
    return path
