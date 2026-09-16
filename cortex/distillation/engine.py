"""Distillation Engine (PRD §8): events -> Normalize -> Segment -> Classify ->
Extract -> Link -> Deduplicate -> Validate -> Confidence -> Persist.

Improvements over v0.1 (Ondas 1-3):
- optional LLM distiller (local Ollama) supplementing heuristics, always at the
  bottom of the inference hierarchy (§8.3) and falling back silently (§42);
- semantic deduplication (token-set similarity) that strengthens existing
  knowledge instead of duplicating it;
- contradiction detection by token similarity, not substring;
- raw-event retention purge after each run;
- every run recorded for observability (§41)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from cortex.distillation import correnda as correnda_mod
from cortex.distillation.extractors import (
    extract_decisions,
    extract_fixes,
    extract_intentions,
    extract_negative_knowledge,
    short_identifier_tokens,
    statement_similarity,
)
from cortex.knowledge.models import (
    ArtifactType,
    Entity,
    Evidence,
    EvidenceStatus,
    EvidenceType,
    Provenance,
    ReviewPolicy,
    RiskLevel,
    Status,
    _utcnow,
    parse_utc,
)
from cortex.storage.store import KnowledgeStore

DEDUP_SIMILARITY = 0.75
FIX_DEDUP_SIMILARITY = 0.90  # distinct fixes are correnda evidence — only near-identical ones merge
CONTRADICTION_SIMILARITY = 0.6


@dataclass
class DistillationReport:
    session_id: str | None = None
    events_processed: int = 0
    intentions: int = 0
    adrs: int = 0
    fixes: int = 0
    negative_knowledge: int = 0
    correndas_proposed: int = 0
    contradictions: int = 0
    deduplicated: int = 0
    below_threshold: int = 0
    purged_events: int = 0
    llm_used: bool = False
    heuristics_failed: bool = False
    unparsed_timestamps: int = 0
    warnings: list[str] = field(default_factory=list)
    new_ids: list[str] = field(default_factory=list)
    extraction_by_source: dict[str, int] = field(default_factory=dict)

    def summary(self) -> str:
        return (
            f"events={self.events_processed} "
            f"intentions={self.intentions} adrs={self.adrs} fixes={self.fixes} "
            f"negative={self.negative_knowledge} correndas_proposed={self.correndas_proposed} "
            f"contradictions={self.contradictions} deduplicated={self.deduplicated} "
            f"below_threshold={self.below_threshold} purged={self.purged_events}"
            + (" llm=on" if self.llm_used else "")
            + (f" unparsed_timestamps={self.unparsed_timestamps}"
               if self.unparsed_timestamps else "")
            + (f" extraction={self.extraction_by_source}" if self.extraction_by_source else "")
        )


class DistillationEngine:
    def __init__(self, store: KnowledgeStore, min_confidence: float = 0.60,
                 correnda_min_evidence: int = 2, retention_days: int = 0,
                 llm: str = "heuristic", ollama_url: str | None = None,
                 llm_model: str | None = None, llm_timeout_s: float | None = None,
                 network_calls: bool = False):
        self.store = store
        self.min_confidence = min_confidence
        self.correnda_min_evidence = correnda_min_evidence
        self.retention_days = retention_days
        self.llm_mode = llm
        self.ollama_url = ollama_url
        self.llm_model = llm_model
        self.llm_timeout_s = llm_timeout_s
        # PRD/README promise: zero outbound network call by default. Ollama
        # on loopback is a local resource, not "the network" — a non-loopback
        # ollama_url is the one path that could actually leave the machine,
        # so it alone is gated behind this flag (item 3.4).
        self.network_calls = network_calls

    # ---- public API ----

    def distill_session(self, session_id: str) -> DistillationReport:
        events = self.store.undistilled_events(session_id)
        return self._run(events, session_id)

    def distill_all(self) -> DistillationReport:
        events = self.store.undistilled_events()
        return self._run(events, None)

    # ---- pipeline ----

    def _run(self, events: list[dict], session_id: str | None) -> DistillationReport:
        report = DistillationReport(session_id=session_id, events_processed=len(events))
        if not events:
            self.store.record_distill_run(session_id, report.summary())
            return report

        candidates = self._extract(events, report)

        existing = self.store.all_entities()

        for cand in candidates:
            if cand.confidence < self.min_confidence:
                report.below_threshold += 1
                continue
            dup = self._find_duplicate(cand, existing)
            if dup is not None:
                report.deduplicated += 1
                self._strengthen(dup, cand)
                continue
            entity = self._persist_candidate(cand)
            existing.append(entity)
            report.new_ids.append(entity.id)
            self._count(report, entity.type)

        self._propose_correndas(report)
        self._detect_contradictions(report)
        self._mark_stale(report)
        if report.heuristics_failed:
            # Evidence survives: leave events un-distilled so the next distill
            # retries them (dedup makes reprocessing safe).
            report.warnings.append(
                f"{len(events)} events left UN-distilled for retry (extraction failed)"
            )
        else:
            self.store.mark_distilled([e["id"] for e in events])
        if self.retention_days > 0:
            report.purged_events = self.store.purge_old_events(self.retention_days)
        self.store.record_distill_run(session_id, report.summary())
        return report

    def _extract(self, events: list[dict], report: DistillationReport) -> list:
        if not events:
            return []

        candidates: list = []
        # One extractor at a time: an isolated failure must not sink the
        # others' output, but any failure keeps the events un-distilled.
        import logging
        extractors = (extract_decisions, extract_intentions,
                      extract_negative_knowledge, extract_fixes)
        failures = 0
        for extractor in extractors:
            try:
                candidates += extractor(events)
            except Exception:
                failures += 1
                logging.getLogger("cortex.distill").warning(
                    "heuristic extractor failed; events left for retry",
                    exc_info=True, extra={"extractor": extractor.__name__},
                )
        if failures:
            report.heuristics_failed = True
        
        # Optional LLM pass supplements heuristics; never replaces explicit
        # statements (PRD §8.3) and never breaks the session (§42).
        if self.llm_mode in ("ollama", "auto"):
            try:
                import logging
                from urllib.parse import urlparse

                from cortex.distillation.llm import OllamaDistiller, llm_candidates
                url = self.ollama_url or "http://localhost:11434"
                host = urlparse(url).hostname or ""
                is_local = host in ("localhost", "127.0.0.1", "::1")
                distiller: OllamaDistiller | None
                if not is_local and not self.network_calls:
                    logging.getLogger("cortex.distill").info(
                        "LLM skipped: ollama_url %s is remote but "
                        "privacy.network_calls=false", host)
                    distiller = None
                else:
                    distiller = OllamaDistiller(
                        url=url,
                        model=self.llm_model or "qwen2.5:7b",
                        timeout=self.llm_timeout_s or 30.0,
                    )
                    # Probe even in explicit mode: a dead Ollama must degrade
                    # with a signal (2s probe) instead of hanging the Stop
                    # hook for the full extract timeout.
                    if not distiller.available():
                        if self.llm_mode == "ollama":
                            logging.getLogger("cortex.distill").info(
                                "llm=ollama but server is down; skipping LLM pass")
                        distiller = None
                if distiller is not None:
                    raw = distiller.extract(events)
                    if raw is not None:
                        report.llm_used = True
                        candidates += llm_candidates(raw, events)
            except Exception:
                # LLM errors should not break the pipeline
                import logging
                logging.getLogger("cortex.distill").warning(
                    "LLM extraction failed, falling back to heuristics", exc_info=True)
        for candidate in candidates:
            report.extraction_by_source[candidate.source] = (
                report.extraction_by_source.get(candidate.source, 0) + 1
            )
        return candidates

    # ---- dedup ----

    def _find_duplicate(self, cand, existing: list[Entity]) -> Entity | None:
        # Fixes with similar symptoms are usually *distinct* evidence (the raw
        # material of Correndas) — merge only near-identical re-observations.
        # O(N²) mitigation: cache similarity calculations within a single distillation
        # run (item 2). The same statement may be compared against multiple existing
        # entities; caching avoids redundant expensive similarity computations.
        threshold = (FIX_DEDUP_SIMILARITY if cand.etype == ArtifactType.FIX
                     else DEDUP_SIMILARITY)
        
        # Per-run similarity cache: maps (cand_statement, ent_statement) -> similarity
        if not hasattr(self, '_similarity_cache'):
            self._similarity_cache = {}
        
        for ent in existing:
            if ent.type != cand.etype:
                continue
            
            cache_key = (cand.statement, ent.statement)
            if cache_key in self._similarity_cache:
                similarity = self._similarity_cache[cache_key]
            else:
                similarity = statement_similarity(cand.statement, ent.statement)
                self._similarity_cache[cache_key] = similarity
            
            if similarity < threshold:
                continue
            # Known gap (docs/adr/2026-09-13-memory-benchmark-waves.md,
            # adv-dedup-absorbs-update): statement_similarity's tokenizer
            # drops <=2-char tokens, so a value that only changes in a short
            # or versioned identifier ("s3-artifacts" -> "s3-artifacts-v2")
            # scores 1.0 and would be silently absorbed into the old entity
            # instead of triggering a state update. When the short tokens
            # the main similarity ignored actually differ, this is a new
            # observation, not a repeated one — let it become its own
            # candidate so the contradiction/supersession pass downstream
            # can see both and record the transition instead of losing it.
            if short_identifier_tokens(cand.statement) != short_identifier_tokens(ent.statement):
                continue
            return ent
        return None

    def _strengthen(self, existing: Entity, cand) -> None:
        """Same knowledge observed again: keep one entity, add the new evidence
        and nudge confidence up (never past human-confirmed levels)."""
        existing.provenance.source_events = list(dict.fromkeys(
            existing.provenance.source_events + cand.event_ids))
        if cand.files:
            existing.provenance.source_files = list(dict.fromkeys(
                existing.provenance.source_files + cand.files))
        event_map = {event["id"]: event for event in self.store.all_events(cand.session_id)}
        known = {item.id for item in existing.evidence}
        for event_id in cand.event_ids:
            if f"ev-{event_id}" in known:
                continue
            existing.evidence.append(Evidence(
                id=f"ev-{event_id}", type=EvidenceType.EVENT, location=event_id,
                fingerprint=_event_fingerprint(event_map.get(event_id)),
                observed_at=(event_map.get(event_id) or {}).get("ts") or _utcnow(),
                status=EvidenceStatus.RESOLVED if event_id in event_map else EvidenceStatus.UNVERIFIABLE,
                verification_method="event_store",
            ))
        existing.confidence = round(min(0.95, existing.confidence + 0.02), 2)
        existing.updated_at = _utcnow()
        self.store.upsert(existing)

    # ---- persistence ----

    def _persist_candidate(self, cand) -> Entity:
        eid = self.store.reserve_entity_id(cand.etype)
        # ADRs from extraction are candidate decisions (PRD §10.2)
        status = Status.CANDIDATE
        if cand.etype == ArtifactType.FIX:
            status = Status.ACTIVE
        if cand.etype == ArtifactType.NEGATIVE_KNOWLEDGE and cand.source == "explicit_user_statement":
            status = Status.ACTIVE
        event_map = {event["id"]: event for event in self.store.all_events(cand.session_id)}
        branch = next((event.get("branch") for event in event_map.values() if event.get("branch")), None)
        details = dict(cand.details)
        details.setdefault("extraction_method", cand.source)
        entity = Entity(
            id=eid,
            type=cand.etype,
            statement=cand.statement,
            status=status,
            authority=cand.authority,
            confidence=cand.confidence,
            risk_level=(RiskLevel.HIGH if cand.etype == ArtifactType.ADR else RiskLevel.MEDIUM),
            review_policy=(ReviewPolicy.HUMAN_CONFIRMATION
                           if cand.etype in (ArtifactType.ADR, ArtifactType.CORRENDA)
                           else ReviewPolicy.MULTIPLE_EVIDENCE),
            observed_at=_utcnow(),
            valid_from=_utcnow() if status == Status.ACTIVE else None,
            branch=branch,
            scope=cand.scope,
            phase=None,
            session_id=cand.session_id,
            details=details,
            provenance=Provenance(
                source_session=cand.session_id,
                source_events=cand.event_ids,
                source_files=cand.files,
                source_commits=cand.commits,
                extraction_source=cand.source,
            ),
        )
        entity.evidence = [Evidence(
            id=f"ev-{event_id}", type=EvidenceType.EVENT, location=event_id,
            fingerprint=_event_fingerprint(event_map.get(event_id)),
            observed_at=(event_map.get(event_id) or {}).get("ts") or _utcnow(),
            status=EvidenceStatus.RESOLVED if event_id in event_map else EvidenceStatus.UNVERIFIABLE,
            verification_method="event_store",
        ) for event_id in cand.event_ids]
        self.store.upsert(entity)
        # graph edges
        if cand.session_id:
            self.store.add_edge(eid, "OCCURRED_IN", cand.session_id)
        for commit in cand.commits:
            self.store.add_edge(eid, "EVIDENCED_BY", commit)
        for file in cand.files[:5]:
            self.store.add_edge(eid, "AFFECTS", f"file:{file}")
        return entity

    def _propose_correndas(self, report: DistillationReport) -> None:
        fixes = self.store.list_by_type(ArtifactType.FIX)
        if len(fixes) < self.correnda_min_evidence:
            return
        used: set[str] = set()
        for cor in self.store.list_by_type(ArtifactType.CORRENDA):
            for _rel, fix in self.store.related(cor.id, rel="EVIDENCED_BY", direction="in"):
                used.add(fix.id)
        groups = correnda_mod.group_recurring_root_causes(
            fixes, min_evidence=self.correnda_min_evidence, already_used=used,
        )
        existing_correndas = self.store.list_by_type(ArtifactType.CORRENDA)
        for g in groups:
            statement = correnda_mod.correnda_statement(g)
            if any(c.statement == statement for c in existing_correndas):
                continue
            cid = self.store.reserve_entity_id(ArtifactType.CORRENDA)
            first = g.fixes[0]
            cor = Entity(
                id=cid,
                type=ArtifactType.CORRENDA,
                statement=statement,
                status=Status.PROPOSED,  # never auto-active (ADR-C3)
                authority=first.authority,
                confidence=g.confidence,
                scope=correnda_mod.correnda_scope(g),
                session_id=first.session_id,
                details={
                    "rule": statement,
                    "origin": [f.id for f in g.fixes],
                    "confirmed_by_human": False,
                    "evidence_similarity": round(g.avg_similarity(), 2),
                },
                provenance=Provenance(
                    source_entities=[f.id for f in g.fixes],
                    source_session=first.session_id,
                    extraction_source="high_confidence_pattern",
                ),
            )
            self.store.upsert(cor)
            for fix_id, rel in correnda_mod.evidence_edges(g):
                self.store.add_edge(fix_id, rel, cid)
            report.correndas_proposed += 1
            report.new_ids.append(cid)

    # ---- contradiction (semantic, Onda 4 & Onda 14) ----

    def _detect_contradictions(self, report: DistillationReport) -> None:
        """Multi-vector semantic contradiction matrix (PRD §17, Onda 14).
        Detects:
        1. ADR Decision vs ADR Rejected Alternative
        2. ADR Decision vs ADR Decision (Direct clash in overlapping scope)
        3. Correnda Rule vs Intention / Decision (Rule violation)
        4. Polar negation / antonym conflict between statements in scope

        Incremental: only entities never checked (or changed since their
        last check, per freshness.contradiction_checked_at) are compared
        against all current entities. Steady-state cost is O(new) per run
        instead of O(N^2) over the whole store; pairs already carrying a
        CONTRADICTS edge are not re-counted (the old pass re-counted every
        stable contradiction on every run, inflating the report forever).
        """
        from cortex.distillation.extractors import (
            dense_semantic_similarity,
            detect_negation_conflict,
            statement_tokens,
        )

        all_active = [
            e for e in self.store.all_entities()
            if e.status in (Status.CANDIDATE, Status.PROPOSED, Status.ACTIVE) and e.is_current
        ]
        unchecked = [e for e in all_active if _needs_contradiction_check(e)]
        if not unchecked:
            return

        def _scope_overlaps(s1: list[str], s2: list[str]) -> bool:
            if not s1 or not s2:
                return True
            for p1 in s1:
                p1_clean = p1.replace("\\", "/").lower()
                for p2 in s2:
                    p2_clean = p2.replace("\\", "/").lower()
                    if p1_clean in p2_clean or p2_clean in p1_clean:
                        return True
            return False

        recorded_pairs: set[tuple[str, str]] = {
            tuple(sorted((e["src"], e["dst"])))
            for e in self.store.edges_of(rel="CONTRADICTS")
        }

        for new in unchecked:
            for old in all_active:
                if new.id == old.id:
                    continue
                pair_key = tuple(sorted([new.id, old.id]))
                if pair_key in recorded_pairs:
                    continue

                if not _scope_overlaps(new.scope, old.scope):
                    continue

                is_contradiction = False
                contradiction_type = None

                similarity = statement_similarity(new.statement, old.statement)
                if similarity >= 0.90:
                    self.store.add_edge(new.id, "DUPLICATES", old.id)
                    continue
                if new.branch and old.branch and new.branch != old.branch:
                    # Same knowledge observed on different branches is a
                    # variant, not a global contradiction. Keep the relation
                    # explicit so review/impact tools can distinguish it.
                    if similarity >= 0.55:
                        self.store.add_edge(new.id, "VARIANT_OF", old.id)
                        continue

                # Vector 1: ADR vs Rejected Alternative
                if new.type == ArtifactType.ADR and old.type == ArtifactType.ADR:
                    dec_tokens = statement_tokens(new.details.get("decision") or new.statement)
                    for alt in old.details.get("alternatives_rejected", []):
                        alt_toks = statement_tokens(alt)
                        if alt_toks and dec_tokens:
                            overlap = len(alt_toks & dec_tokens) / len(alt_toks)
                            if overlap >= CONTRADICTION_SIMILARITY:
                                is_contradiction = True
                                contradiction_type = "direct_decision_clash"
                                break

                # Vector 2: Polar Negation / Antonym Conflict
                if not is_contradiction and detect_negation_conflict(new.statement, old.statement):
                    is_contradiction = True
                    contradiction_type = "direct_contradiction"

                if (not is_contradiction and new.type == old.type == ArtifactType.ADR
                        and new.details.get("context") and old.details.get("context")
                        and dense_semantic_similarity(new.details["context"], old.details["context"]) < 0.35
                        and similarity >= 0.35):
                    is_contradiction = True
                    contradiction_type = "changed_premise"

                # Vector 3: Correnda Rule vs Decision / Intention Conflict
                if not is_contradiction and old.type == ArtifactType.CORRENDA and new.type in (ArtifactType.ADR, ArtifactType.INTENTION):
                    rule = old.details.get("rule") or old.statement
                    if detect_negation_conflict(new.statement, rule) or dense_semantic_similarity(new.statement, rule) >= 0.70:
                        is_contradiction = True
                        contradiction_type = "rule_conflict"

                if is_contradiction:
                    recorded_pairs.add(pair_key)
                    self.store.add_edge(new.id, "CONTRADICTS", old.id)
                    report.contradictions += 1

                    # Flag contradiction pending review in details
                    new.details["contradiction_pending"] = True
                    old.details["contradiction_pending"] = True
                    new.details["contradiction_type"] = contradiction_type or "semantic_conflict"
                    old.details["contradiction_type"] = contradiction_type or "semantic_conflict"
                    self.store.upsert(new)
                    self.store.upsert(old)
            # Stamp after the full pass so the flag mutation above is included;
            # updated_at is not bumped here, so the stamp is not self-invalidating.
            new.freshness.contradiction_checked_at = _utcnow()
            self.store.upsert(new)


    def _mark_stale(self, report: DistillationReport) -> None:
        """PRD §46: stale memories stop being default-context candidates."""
        for ent in self.store.all_entities():
            if ent.freshness.stale:
                continue
            verified = ent.freshness.last_verified_at or ent.updated_at
            age = _days_since(verified)
            if age is None:
                # Unparsable timestamp must not fake freshness (would mean the
                # entity never ages); skip and surface instead.
                report.unparsed_timestamps += 1
                continue
            if age > ent.freshness.stale_after_days:
                ent.freshness.stale = True
                self.store.upsert(ent)

    def _count(self, report: DistillationReport, etype: ArtifactType) -> None:
        mapping = {
            ArtifactType.INTENTION: "intentions",
            ArtifactType.ADR: "adrs",
            ArtifactType.FIX: "fixes",
            ArtifactType.NEGATIVE_KNOWLEDGE: "negative_knowledge",
        }
        attr = mapping.get(etype)
        if attr:
            setattr(report, attr, getattr(report, attr) + 1)


def _needs_contradiction_check(e: Entity) -> bool:
    """True when the entity must (re)enter the contradiction pass: never
    checked, or created/updated after its last check. `upsert` refreshes
    updated_at, so any later mutation re-triggers the check — including the
    contradiction_pending flag itself, which is intentional: the next run
    re-validates flagged pairs until a human resolves them."""
    checked = parse_utc(e.freshness.contradiction_checked_at or "")
    updated = parse_utc(e.updated_at)
    if checked is None or updated is None:
        return True
    return updated > checked


def _days_since(ts: str) -> float | None:
    dt = parse_utc(ts)
    if dt is None:
        return None  # caller skips the entity and counts it — never fakes freshness
    return (datetime.now(UTC) - dt).days


def _event_fingerprint(event: dict | None) -> str | None:
    if not event:
        return None
    import hashlib
    payload = f"{event.get('id')}|{event.get('type')}|{event.get('content') or ''}"
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()
