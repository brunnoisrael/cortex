"""Context Compiler (PRD §18): persistent knowledge -> small, high-value context.

score = semantic_relevance x scope_match x authority_weight x confidence
        x freshness x task_similarity                         (PRD §18.3)
"""

from __future__ import annotations

import functools
import logging
from dataclasses import dataclass
from typing import cast

from cortex.distillation.extractors import dense_semantic_similarity
from cortex.knowledge.models import (
    AUTHORITY_WEIGHT,
    ArtifactType,
    Entity,
    Status,
)
from cortex.storage.store import KnowledgeStore

# A rejected decision matters because it prevents regression (PRD §44.4):
# negative knowledge and superseded history stay queryable but out of default context.
CONTEXT_ELIGIBLE_TYPES = (
    ArtifactType.INTENTION,
    ArtifactType.ADR,
    ArtifactType.FIX,
    ArtifactType.CORRENDA,
    ArtifactType.NEGATIVE_KNOWLEDGE,
)


@dataclass
class CompileInput:
    query: str = ""
    files: list[str] | None = None
    branch: str | None = None
    phase: str | None = None
    profile: str = "default"


COMPILATION_PROFILES: dict[str, dict[str, object]] = {
    "default": {},
    "bug_fix": {"include_recent_fixes": True, "include_last_review": True},
    "architecture_review": {"max_adrs": 10, "max_correndas": 10, "include_recent_fixes": False},
    "onboarding": {"max_intentions": 10, "max_adrs": 8, "max_correndas": 8},
    "session_resume": {"include_last_review": True, "include_recent_fixes": True},
}


@dataclass
class RankedItem:
    entity: Entity
    score: float
    reasons: dict


def scope_match(entity_scope: list[str], files: list[str] | None) -> float:
    if not files:
        return 0.8  # unknown scope: neutral-ish
    if not entity_scope:
        return 0.6
    score = 0.4
    for path in files:
        norm = path.replace("\\", "/").lower()
        for s in entity_scope:
            snorm = s.lower()
            if norm.startswith(snorm) or snorm in norm:
                score = 1.0
                break
    return score


def _word_tokens(text: str) -> set[str]:
    import re
    return {t for t in re.findall(r"[a-zá-úà-ùâ-ûã-õç0-9]+", text.lower()) if len(t) > 2}


def keyword_overlap(query: str, text: str) -> float:
    if not query.strip():
        return 0.5
    q_tokens = _word_tokens(query)
    if not q_tokens:
        return 0.5
    t_tokens = _word_tokens(text)
    return len(q_tokens & t_tokens) / len(q_tokens)


def content_density(text: str) -> float:

    """Calculate technical signal density (identifiers, paths, technical terms vs fluff)."""
    import re
    if not text.strip():
        return 0.5
    tokens = re.findall(r"[A-Za-z0-9_\-\./\\]+", text)
    if not tokens:
        return 0.5
    tech_tokens = [t for t in tokens if len(t) > 2 and (
        "_" in t or "/" in t or "." in t or any(c.isupper() for c in t[1:]) or any(c.isdigit() for c in t)
    )]
    ratio = len(tech_tokens) / len(tokens)
    return round(min(1.0, 0.4 + ratio * 1.2), 2)


def rank(
    store: KnowledgeStore,
    inp: CompileInput,
    limit: int = 20,
    federated_stores: list[KnowledgeStore] | None = None,
    weights_override: dict[str, float] | None = None,
) -> list[RankedItem]:
    if limit <= 0 or limit > 100:
        limit = 20  # Safe default
        
    files = inp.files or []
    stores = [store] + (federated_stores or [])

    # Onda 12 & Onda 13: Weight auto-calibration and hybrid search parameters
    w = {
        "authority": 1.0,
        "freshness": 1.0,
        "ast_boost": 1.25,
        "sparse": 0.55,
        "dense": 0.45,
        "density": 0.25,
    }
    if weights_override:
        unknown = set(weights_override) - set(w)
        if unknown:
            raise ValueError(
                f"rank(): unknown weight key(s) {sorted(unknown)}; valid keys are "
                f"{sorted(w)} (a typo here would silently be ignored otherwise)"
            )
        w.update(weights_override)

    items: list[RankedItem] = []
    for s_idx, st in enumerate(stores):
        is_federated = s_idx > 0
        candidates: list[Entity] = []
        fts: dict[str, float] = {}
        if inp.query.strip():
            try:
                results = st.search(inp.query, limit=200)
                if results:
                    mx = max(s for _, s in results) or 1.0
                    fts = {e.id: s / mx for e, s in results}
            except Exception:
                logging.getLogger("cortex.compiler").warning(
                    "FTS search failed for store %s; ranking continues without it",
                    getattr(st, "db_path", st), exc_info=True,
                )
                fts = {}

        for ent in st.all_entities():
            if ent.type not in CONTEXT_ELIGIBLE_TYPES:
                continue
            if not ent.is_current or ent.freshness.stale or not ent.is_valid_now:
                continue
            candidates.append(ent)
        if not candidates:
            continue

        # Batched graph signals: one grouped query each for the whole
        # candidate set (was one query per entity inside the scoring loop).
        degrees = st.node_degrees([e.id for e in candidates])
        contradicted_ids = st.contradicted_by_active([e.id for e in candidates])

        for ent in candidates:

            full_text = ent.statement + " " + " ".join(ent.scope) + " " + " ".join(
                str(v) for v in ent.details.values() if isinstance(v, str)
            )

            # 1. Hybrid Search (Sparse BM25/Jaccard + Dense Subword/Embedding Cosine)
            # Optimized to avoid repeated calculations
            if inp.query.strip():
                keyword_scores = [
                    fts.get(ent.id, 0.0),
                    keyword_overlap(inp.query, ent.statement + " " + " ".join(ent.scope))
                ]
                keyword_scores.extend(
                    keyword_overlap(inp.query, str(v)) for v in ent.details.values() if isinstance(v, str)
                )
                sparse_score = max(keyword_scores)
                dense_score = dense_semantic_similarity(inp.query, full_text)
            else:
                sparse_score = 0.5
                dense_score = 0.5

            hybrid_relevance = (w["sparse"] * sparse_score) + (w["dense"] * dense_score)

            if inp.query.strip() and hybrid_relevance < 0.05:
                sm = scope_match(ent.scope, files)
                if sm < 0.5:
                    continue

            # 2. Knowledge Graph & Content Signal Density
            graph_deg = degrees.get(ent.id, 0)
            graph_density = min(1.0, graph_deg / 4.0)
            c_density = content_density(full_text)
            density_multiplier = 1.0 + w["density"] * (0.6 * graph_density + 0.4 * c_density)

            # 3. Revalidation Phase (Contradictions + Authority + Freshness + Scope)
            authority_weight = AUTHORITY_WEIGHT.get(ent.authority, 0.5) * w["authority"]
            if getattr(ent.freshness, "verification_source", None) == "ast":
                authority_weight *= w["ast_boost"]

            # Contradiction Penalty Revalidation: entity contradicted by an
            # ACTIVE entity (pre-computed for the whole candidate set above).
            contradiction_penalty = 1.0
            contradicted = ent.id in contradicted_ids
            if contradicted:
                contradiction_penalty = 0.35

            freshness = (0.5 if ent.freshness.last_verified_at else 0.85) * w["freshness"]
            fed_mult = 0.9 if is_federated else 1.0

            score = (
                hybrid_relevance
                * density_multiplier
                * scope_match(ent.scope, files)
                * authority_weight
                * ent.confidence
                * freshness
                * contradiction_penalty
                * fed_mult
            )

            items.append(RankedItem(
                entity=ent,
                score=round(score, 4),
                reasons={
                    "relevance": round(hybrid_relevance, 2),
                    "sparse": round(sparse_score, 2),
                    "dense": round(dense_score, 2),
                    "graph_density": round(graph_density, 2),
                    "content_density": round(c_density, 2),
                    "authority": ent.authority.value,
                    "confidence": ent.confidence,
                    "federated": is_federated,
                    "ast_verified": getattr(ent.freshness, "verification_source", None) == "ast",
                    "contradicted": contradicted,
                    "contradiction_penalty": contradiction_penalty,
                    "scope_match": round(scope_match(ent.scope, files), 2),
                    "authority_weight": round(authority_weight, 3),
                    "freshness": round(freshness, 3),
                }
            ))

    items.sort(key=lambda i: i.score, reverse=True)
    return items[:limit]


def _get_encoding():
    """Lazy-load tiktoken encoding for cl100k_base (GPT-4/3.5-turbo compatible)."""
    try:
        import tiktoken
        return tiktoken.get_encoding("cl100k_base")
    except Exception:
        return None


@functools.lru_cache(maxsize=1)
def _get_encoding_cached():
    return _get_encoding()


def token_estimate(text: str) -> int:
    """Accurate token estimate using tiktoken cl100k_base (GPT-4/3.5-turbo).

    Falls back to ~1.4 tokens/word heuristic if tiktoken unavailable.
    Public so tests can assert against the actual estimator production uses.
    """
    if not text or not isinstance(text, str):
        return 0
    enc = _get_encoding_cached()
    if enc is not None:
        try:
            return max(1, len(enc.encode(text)))
        except Exception:
            pass
    # Fallback: ~1.4 tokens/word for PT/EN morphology
    return max(1, int(len(text.split()) * 1.4))


_tokens = token_estimate  # backwards-compat alias; cli/app.py imports this name


def compile_context(store: KnowledgeStore, inp: CompileInput,
                    max_tokens: int = 2000, max_adrs: int = 5, max_intentions: int = 5,
                    max_correndas: int = 7, include_recent_fixes: bool = True,
                    include_last_review: bool = True) -> str:
    """Render the CORTEX CONTEXT block within the token budget (PRD §18.4)."""
    profile = COMPILATION_PROFILES.get(inp.profile, {})
    max_adrs = int(cast(int, profile.get("max_adrs", max_adrs)))
    max_intentions = int(cast(int, profile.get("max_intentions", max_intentions)))
    max_correndas = int(cast(int, profile.get("max_correndas", max_correndas)))
    include_recent_fixes = bool(profile.get("include_recent_fixes", include_recent_fixes))
    include_last_review = bool(profile.get("include_last_review", include_last_review))
    try:
        ranked = rank(store, inp)
    except Exception:
        return _minimal_safe_context(store)  # PRD §42: never block the session

    END_MARKER = "<!-- END CORTEX CONTEXT -->"
    block = ["<!-- CORTEX CONTEXT -->"]

    def fits(line: str) -> bool:
        # Estimate the exact rendered block.  Tokenizers can encode a line
        # differently when it is adjacent to a newline, so summing per-line
        # estimates is not sufficient for a hard budget.
        return token_estimate("\n".join(block + [line, END_MARKER])) <= max_tokens

    def add(line: str) -> None:
        block.append(line)

    def provenance_hint(entity: Entity) -> str:
        resolved = [item for item in entity.evidence if item.status.value == "resolved"]
        if resolved:
            item = resolved[0]
            location = f"{item.location}:{item.line_start}" if item.line_start else item.location
            return f" (source: {location})"
        if entity.provenance.source_files:
            return f" (source: {entity.provenance.source_files[0]})"
        return ""

    if token_estimate("\n".join(block + [END_MARKER])) > max_tokens:
        return END_MARKER

    emit_directive = "[DIRECTIVE] When making architectural decisions, rejecting alternatives, or fixing bugs, invoke `cortex_emit` to record structured knowledge."
    if fits(emit_directive):
        add(emit_directive)

    if inp.branch:
        line = f"BRANCH: {inp.branch}"
        if fits(line):
            add(line)

    intentions = [r for r in ranked if r.entity.type == ArtifactType.INTENTION][:max_intentions]
    if intentions and fits("ACTIVE INTENTIONS"):
        add("ACTIVE INTENTIONS")
        for r in intentions:
            line = f"- [{r.entity.id}] {r.entity.statement}{provenance_hint(r.entity)}"
            if not fits(line):
                break
            add(line)

    adrs = [r for r in ranked if r.entity.type == ArtifactType.ADR][:max_adrs]
    if adrs and fits("RELEVANT ADRS"):
        add("RELEVANT ADRS")
        for r in adrs:
            decision = r.entity.details.get("decision") or r.entity.statement
            line = f"- [{r.entity.id}] {decision}{provenance_hint(r.entity)}"
            rejected = r.entity.details.get("alternatives_rejected") or []
            if rejected:
                line += f" (rejected alternatives: {', '.join(rejected)})"
            if not fits(line):
                break
            add(line)

    correndas = [r for r in ranked if r.entity.type == ArtifactType.CORRENDA][:max_correndas]
    if correndas and fits("ACTIVE CORRENDAS"):
        add("ACTIVE CORRENDAS")
        for r in correndas:
            suffix = "" if r.entity.status == Status.ACTIVE else f" (status: {r.entity.status.value})"
            line = f"- [{r.entity.id}] {r.entity.statement}{suffix}{provenance_hint(r.entity)}"
            if not fits(line):
                break
            add(line)

    negatives = [r for r in ranked if r.entity.type == ArtifactType.NEGATIVE_KNOWLEDGE]
    if negatives and fits("NEGATIVE KNOWLEDGE (do not repeat)"):
        add("NEGATIVE KNOWLEDGE (do not repeat)")
        for r in negatives:
            line = f"- [{r.entity.id}] {r.entity.statement}{provenance_hint(r.entity)}"
            if not fits(line):
                break
            add(line)

    if include_recent_fixes:
        fixes = [r for r in ranked if r.entity.type == ArtifactType.FIX][:3]
        if fixes and fits("RECENT FIXES"):
            add("RECENT FIXES")
            for r in fixes:
                line = f"- [{r.entity.id}] {r.entity.details.get('symptom', r.entity.statement)}{provenance_hint(r.entity)}"
                if not fits(line):
                    break
                add(line)

    if include_last_review:
        reviews = sorted(
            (e for e in store.list_by_type(ArtifactType.REVIEW)),
            key=lambda e: e.created_at,
        )
        if reviews:
            last = reviews[-1]
            threads = last.details.get("open_threads") or []
            if threads and fits("OPEN THREADS"):
                add("OPEN THREADS")
                for t in threads[:3]:
                    line = f"- {t}"
                    if not fits(line):
                        break
                    add(line)

    block.append(END_MARKER)
    return "\n".join(block)


def retrieval_trace(
    store: KnowledgeStore,
    inp: CompileInput,
    *,
    limit: int = 20,
    budget: int | None = None,
    selected_ids: set[str] | None = None,
) -> dict:
    """Return a stable explanation of retrieval and exclusion decisions."""
    eligible_types = {item.value for item in CONTEXT_ELIGIBLE_TYPES}
    candidates = []
    excluded: list[dict[str, object]] = []
    recovered_ids: set[str] = set()
    if inp.query.strip():
        try:
            recovered_ids.update(entity.id for entity, _score in store.search(inp.query, limit=200))
        except Exception:
            excluded.append({"id": "<fts>", "reason": "retrieval_failure"})
    for entity in store.all_entities():
        reason = None
        if entity.type.value not in eligible_types:
            reason = "type_not_context_eligible"
        elif not entity.is_current:
            reason = "non_current_status"
        elif entity.freshness.stale:
            reason = "stale"
        elif not entity.is_valid_now:
            reason = "outside_validity_interval"
        if reason:
            excluded.append({"id": entity.id, "reason": reason})
        else:
            candidates.append(entity.id)
            recovered_ids.add(entity.id)
    ranked = rank(store, inp, limit=limit)
    if selected_ids is None:
        selected_ids = {item.entity.id for item in ranked}
    ranked_rows = [{
        "id": item.entity.id,
        "score": item.score,
        "reasons": item.reasons,
        "selected": item.entity.id in selected_ids,
    } for item in ranked]
    for item in ranked:
        if item.entity.id not in selected_ids:
            excluded.append({"id": item.entity.id, "reason": "not_selected_by_limit"})
    if budget is not None:
        estimated = 0
        for item in ranked:
            text = f"[{item.entity.id}] {item.entity.statement}"
            cost = token_estimate(text)
            if item.entity.id in selected_ids:
                estimated += cost
                if estimated > budget:
                    excluded.append({"id": item.entity.id, "reason": "budget", "estimated_tokens": cost})
    return {
        "schema": "retrieval_trace/v1",
        "query": inp.query,
        "profile": inp.profile,
        "signals": {"sparse": 0.55, "dense": 0.45, "authority": 1.0, "freshness": 1.0,
                     "ast_boost": 1.25, "density": 0.25},
        "recovered_ids": sorted(recovered_ids),
        "recovered_count": len(recovered_ids),
        "candidate_count": len(candidates),
        "eligible_ids": sorted(candidates),
        "ranked": ranked_rows,
        "excluded": sorted(excluded, key=lambda row: (row["id"], row["reason"])),
        "budget": budget,
        "budget_evaluation": budget_evaluation(ranked, selected_ids, budget),
    }


def budget_evaluation(ranked: list[RankedItem], selected_ids: set[str], budget: int | None) -> dict:
    """Summarize utility/token tradeoffs and risky/duplicated context items."""
    selected = [item for item in ranked if item.entity.id in selected_ids]
    costs = {item.entity.id: token_estimate(f"[{item.entity.id}] {item.entity.statement}") for item in selected}
    statements = [item.entity.statement.casefold().strip() for item in selected]
    duplicates = len(statements) - len(set(statements))
    total = sum(costs.values())
    high_risk = [item.entity.id for item in selected if item.entity.risk_level.value == "high"]
    utility = sum(item.score for item in selected)
    return {
        "estimated_tokens": total,
        "within_budget": budget is None or total <= budget,
        "utility": round(utility, 4),
        "utility_per_token": round(utility / max(1, total), 6),
        "high_risk_selected": high_risk,
        "duplicate_items": duplicates,
        "cost_by_id": costs,
    }


def compile_context_with_trace(store: KnowledgeStore, inp: CompileInput, **kwargs) -> dict:
    """Compile context and return the rendered block plus its audit trace."""
    context = compile_context(store, inp, **kwargs)
    selected = {line.split("]", 1)[0][3:] for line in context.splitlines() if line.startswith("- [") and "]" in line}
    trace = retrieval_trace(store, inp, budget=kwargs.get("max_tokens"), selected_ids=selected)
    trace["selected_ids"] = sorted(selected)
    trace["estimated_context_tokens"] = token_estimate(context)
    return {"context": context, "trace": trace}


def _minimal_safe_context(store: KnowledgeStore) -> str:
    """PRD §42: on compile failure return minimal safe context."""
    lines = ["<!-- CORTEX CONTEXT -->", "MINIMAL SAFE CONTEXT (compile failed)"]
    for ent in store.list_by_type(ArtifactType.ADR):
        if ent.status == Status.ACTIVE:
            lines.append(f"- ADR [{ent.id}] {ent.statement}")
    lines.append("<!-- END CORTEX CONTEXT -->")
    return "\n".join(lines)
