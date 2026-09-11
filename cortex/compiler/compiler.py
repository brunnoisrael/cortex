"""Context Compiler (PRD §18): persistent knowledge -> small, high-value context.

score = semantic_relevance x scope_match x authority_weight x confidence
        x freshness x task_similarity                         (PRD §18.3)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

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
            if not ent.is_current or ent.freshness.stale:
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
                }
            ))

    items.sort(key=lambda i: i.score, reverse=True)
    return items[:limit]




def token_estimate(text: str) -> int:
    """Rough token estimate used for context-budget accounting (PRD §18.4).

    ~1.4 tokens/word accounts for PT/EN morphology better than chars/4.
    Public (renamed from `_tokens`, item 5.2) so tests can assert against
    the actual estimator production uses, instead of duplicating a
    different one and asserting on that."""
    if not text or not isinstance(text, str):
        return 0
    return max(1, int(len(text.split()) * 1.4))


_tokens = token_estimate  # backwards-compat alias; cli/app.py imports this name


def compile_context(store: KnowledgeStore, inp: CompileInput,
                    max_tokens: int = 2000, max_adrs: int = 5, max_intentions: int = 5,
                    max_correndas: int = 7, include_recent_fixes: bool = True,
                    include_last_review: bool = True) -> str:
    """Render the CORTEX CONTEXT block within the token budget (PRD §18.4)."""
    try:
        ranked = rank(store, inp)
    except Exception:
        return _minimal_safe_context(store)  # PRD §42: never block the session

    END_MARKER = "<!-- END CORTEX CONTEXT -->"
    block = ["<!-- CORTEX CONTEXT -->"]
    used = sum(token_estimate(ln) for ln in block)
    # The end marker is appended unconditionally below, after every fits()
    # check has already run — reserve its cost up front so the last body
    # line admitted still leaves room for it (item: END-marker budget).
    end_marker_cost = token_estimate(END_MARKER)

    def fits(line: str) -> bool:
        return used + token_estimate(line) + end_marker_cost <= max_tokens

    def add(line: str) -> None:
        nonlocal used
        block.append(line)
        used += token_estimate(line)

    emit_directive = "[DIRECTIVE] When making architectural decisions, rejecting alternatives, or fixing bugs, invoke `cortex_emit` to record structured knowledge."
    if fits(emit_directive):
        add(emit_directive)

    if inp.branch:
        line = f"BRANCH: {inp.branch}"
        if fits(line):
            add(line)

    intentions = [r for r in ranked if r.entity.type == ArtifactType.INTENTION][:max_intentions]
    if intentions:
        add("ACTIVE INTENTIONS")
        for r in intentions:
            line = f"- [{r.entity.id}] {r.entity.statement}"
            if not fits(line):
                break
            add(line)

    adrs = [r for r in ranked if r.entity.type == ArtifactType.ADR][:max_adrs]
    if adrs:
        add("RELEVANT ADRS")
        for r in adrs:
            decision = r.entity.details.get("decision") or r.entity.statement
            line = f"- [{r.entity.id}] {decision}"
            rejected = r.entity.details.get("alternatives_rejected") or []
            if rejected:
                line += f" (rejected alternatives: {', '.join(rejected)})"
            if not fits(line):
                break
            add(line)

    correndas = [r for r in ranked if r.entity.type == ArtifactType.CORRENDA][:max_correndas]
    if correndas:
        add("ACTIVE CORRENDAS")
        for r in correndas:
            suffix = "" if r.entity.status == Status.ACTIVE else f" (status: {r.entity.status.value})"
            line = f"- [{r.entity.id}] {r.entity.statement}{suffix}"
            if not fits(line):
                break
            add(line)

    negatives = [r for r in ranked if r.entity.type == ArtifactType.NEGATIVE_KNOWLEDGE]
    if negatives:
        add("NEGATIVE KNOWLEDGE (do not repeat)")
        for r in negatives:
            line = f"- [{r.entity.id}] {r.entity.statement}"
            if not fits(line):
                break
            add(line)

    if include_recent_fixes:
        fixes = [r for r in ranked if r.entity.type == ArtifactType.FIX][:3]
        if fixes:
            add("RECENT FIXES")
            for r in fixes:
                line = f"- [{r.entity.id}] {r.entity.details.get('symptom', r.entity.statement)}"
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
            if threads:
                add("OPEN THREADS")
                for t in threads[:3]:
                    line = f"- {t}"
                    if not fits(line):
                        break
                    add(line)

    block.append(END_MARKER)  # reserved above; never re-checked against fits()
    used += end_marker_cost
    return "\n".join(block)


def _minimal_safe_context(store: KnowledgeStore) -> str:
    """PRD §42: on compile failure return minimal safe context."""
    lines = ["<!-- CORTEX CONTEXT -->", "MINIMAL SAFE CONTEXT (compile failed)"]
    for ent in store.list_by_type(ArtifactType.ADR):
        if ent.status == Status.ACTIVE:
            lines.append(f"- ADR [{ent.id}] {ent.statement}")
    lines.append("<!-- END CORTEX CONTEXT -->")
    return "\n".join(lines)