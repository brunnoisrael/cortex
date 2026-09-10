"""Service layer: orchestration shared by the CLI, the MCP server, and the
hook adapter.

The three frontends used to construct DistillationEngine (8 parameters),
find the latest open session, and compute phase-health indicators
independently — three near-identical copies of the same wiring that could
drift apart (and had: the MCP phase tool omitted indicators the CLI showed).
Every frontend builds its objects through these functions so behavior
changes land once.
"""

from __future__ import annotations

from cortex.config import CortexConfig
from cortex.distillation.engine import DistillationEngine
from cortex.knowledge.models import ArtifactType, Status
from cortex.storage.store import KnowledgeStore


def build_distillation_engine(store: KnowledgeStore, cfg: CortexConfig,
                              llm_timeout_cap: float | None = None) -> DistillationEngine:
    """One DistillationEngine constructor for all frontends.

    `llm_timeout_cap` clamps the LLM timeout for latency-sensitive callers
    (the Stop hook caps to 10s so a dead Ollama can't hold the host session).
    """
    timeout = float(cfg.llm_timeout_s)
    if llm_timeout_cap is not None:
        timeout = min(timeout, llm_timeout_cap)
    return DistillationEngine(
        store,
        min_confidence=cfg.min_confidence_for_persistence,
        correnda_min_evidence=cfg.correnda_min_evidence,
        retention_days=cfg.raw_retention_days,
        llm=cfg.llm,
        ollama_url=cfg.ollama_url,
        llm_model=cfg.llm_model,
        llm_timeout_s=timeout,
        network_calls=cfg.network_calls,
    )


def latest_open_session_id(store: KnowledgeStore) -> str | None:
    """The most recently started session that has not ended — the default
    target for `review` / `cortex_review` when no id is given."""
    row = store.conn.execute(
        "SELECT id FROM sessions WHERE ended_at IS NULL ORDER BY started_at DESC LIMIT 1"
    ).fetchone()
    return row["id"] if row else None


def phase_health(store: KnowledgeStore) -> dict:
    """Long-range knowledge-health indicators (PRD §13.2) as plain data —
    the CLI renders them as text, the MCP server as JSON."""
    ents = store.all_entities()
    adrs = [e for e in ents if e.type == ArtifactType.ADR]
    correndas = [e for e in ents if e.type == ArtifactType.CORRENDA]
    stale = [e for e in ents if e.freshness.stale]
    return {
        "adr_total": len(adrs),
        "adr_candidates": len([e for e in adrs if e.status == Status.CANDIDATE]),
        "superseded": len([e for e in ents if e.status == Status.SUPERSEDED]),
        "correndas_total": len(correndas),
        "correndas_active": len([c for c in correndas if c.status == Status.ACTIVE]),
        "correndas_proposed": len([c for c in correndas if c.status == Status.PROPOSED]),
        "stale": len(stale),
        "total_entities": len(ents),
        "knowledge_freshness_pct": 100 - (100 * len(stale) // max(1, len(ents))),
    }
