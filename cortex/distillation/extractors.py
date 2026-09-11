"""Heuristic extractors: raw events -> knowledge candidates (PRD §8).

Inference hierarchy (PRD §8.3): explicit user statement > explicit agent
statement > code/git evidence > pattern > LLM inference.
"""

from __future__ import annotations

import functools
import os
import re
from dataclasses import dataclass, field

from cortex.knowledge.models import (
    CONFIDENCE_BY_SOURCE,
    ArtifactType,
    Authority,
)

# ---- language patterns (PT + EN, per PRD examples) ----

DECISION_RE = re.compile(
    r"\b(vamos usar|usaremos|decidimos|decisão|escolhemos|adotaremos|"
    r"migrar para|migração para|switch to|trocar para|"
    r"we (?:will|'ll) use|we use|we decided|decision|chose|let's use|going with)\b",
    re.IGNORECASE,
)
RATIONALE_RE = re.compile(
    r"\b(porque|por que|motivo|razão|para que|garantir|evitar|"
    r"because|since|so that|in order to|to avoid|to ensure)\b[:,]?\s*(.+)",
    re.IGNORECASE,
)
ALTERNATIVE_RE = re.compile(
    r"\b(em vez de|ao invés de|no lugar de|instead of|rather than|prefer\s+\w+\s+over)"
    r"\s+([A-Za-z0-9_\-\.]{2,40})",
    re.IGNORECASE,
)
INTENTION_RE = re.compile(
    r"\b(objetivo|intent|intenção|queremos|we want|we need|precisamos|precisa permitir|"
    r"para permitir|isolar|isolate|separar|abstrair|so that the system|goal)\b",
    re.IGNORECASE,
)
NEGATIVE_RE = re.compile(
    r"\b(não usar|não utilize|não usaremos|não recomend|não vamos usar|não vamos adotar|"
    r"não vamos migrar|don't use|do not use|avoid using|never use|"
    r"we will not use|we won't use|we decided not to use|rejected? because)\b"
    r"\s+([A-Za-z0-9_\-\.]{2,40})",
    re.IGNORECASE,
)
FIX_MARKER_RE = re.compile(
    r"\b(fix|fixo|corrigido|corrigindo|correção|hotfix|patch|resolved|resolvido|"
    r"corrige|bugfix|workaround|guard clause|validação|validation added)\b",
    re.IGNORECASE,
)
ROOT_CAUSE_RE = re.compile(
    r"\b(causa|root cause|porque|pois|because|due to|caused by|originado de)\b[:,]?\s*(.+)",
    re.IGNORECASE,
)
ERROR_EVENT_TYPES = {"error", "test_failure"}
RESOLUTION_EVENT_TYPES = {"agent_response", "commit", "user_instruction", "tool_result"}


@dataclass
class Candidate:
    etype: ArtifactType
    statement: str
    details: dict
    scope: list[str]
    source: str  # key into CONFIDENCE_BY_SOURCE
    session_id: str | None
    event_ids: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    commits: list[str] = field(default_factory=list)

    @property
    def confidence(self) -> float:
        return CONFIDENCE_BY_SOURCE.get(self.source, 0.65)

    @property
    def authority(self) -> Authority:
        if self.source == "explicit_user_statement":
            return Authority.HUMAN_CONFIRMED
        if self.source == "explicit_agent_statement":
            return Authority.AGENT_INFERRED
        return Authority.OBSERVED


def _is_user(e: dict) -> bool:
    return e["type"] == "user_instruction"


def _top_dirs(files: list[str], depth: int = 2) -> list[str]:
    out = []
    for f in files or []:
        parts = re.split(r"[\\/]", f)
        if len(parts) >= depth:
            out.append("/".join(parts[:depth]))
        elif parts and parts[0]:
            out.append(parts[0])
    return sorted(set(out))


def _clean(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def extract_decisions(events: list[dict]) -> list[Candidate]:
    """User/agent/commit decision statements -> ADR candidates.

    Commit messages count as git evidence (PRD §8.3 tier 3), so they get a
    lower confidence than explicit statements."""
    out: list[Candidate] = []
    for e in events:
        if e["type"] not in ("user_instruction", "agent_response", "commit"):
            continue
        text = _clean(e.get("content"))
        if not text or not DECISION_RE.search(text):
            continue
        # Negation-first: "não vamos usar X" / "we decided not to use X"
        # matches DECISION_RE's verb ("vamos usar"/"we decided") but asserts
        # the *rejection* of X — that is negative knowledge, not an ADR
        # claiming X. extract_negative_knowledge owns those events.
        if NEGATIVE_RE.search(text):
            continue
        if e["type"] == "commit":
            source = "code_git_evidence"
        elif _is_user(e):
            source = "explicit_user_statement"
        else:
            source = "explicit_agent_statement"
        ctx_match = RATIONALE_RE.search(text)
        context = ctx_match.group(2).strip() if ctx_match else text
        alternatives = [m.group(2).strip(" .") for m in ALTERNATIVE_RE.finditer(text)]
        # subject: strip the decision verb, keep the rest
        subject = DECISION_RE.sub("", text, count=1).strip(" :,.")
        subject = subject[:160] if subject else text[:160]
        commits = []
        if e["type"] == "commit":
            commits = [str((e.get("meta") or {}).get("hash") or e["id"])]
        out.append(Candidate(
            etype=ArtifactType.ADR,
            statement=f"Decisão: {subject}",
            details={
                "context": context[:400],
                "decision": subject,
                "alternatives_rejected": alternatives,
                "consequences": [],
            },
            scope=_top_dirs(e.get("files")),
            source=source,
            session_id=e.get("session_id"),
            event_ids=[e["id"]],
            files=list(e.get("files") or []),
            commits=commits,
        ))
    return out


def extract_intentions(events: list[dict]) -> list[Candidate]:
    out: list[Candidate] = []
    for e in events:
        text = _clean(e.get("content"))
        # session_start content is the task that opened the session — the most
        # explicit intention signal there is (Onda 3, item 10)
        if e["type"] == "session_start":
            if text:
                out.append(Candidate(
                    etype=ArtifactType.INTENTION,
                    statement=text[:200],
                    details={"motivation": ""},
                    scope=_top_dirs(e.get("files")),
                    source="explicit_user_statement",
                    session_id=e.get("session_id"),
                    event_ids=[e["id"]],
                    files=list(e.get("files") or []),
                ))
            continue
        if e["type"] not in ("user_instruction", "agent_response"):
            continue
        if not text or not INTENTION_RE.search(text):
            continue
        if DECISION_RE.search(text):
            continue  # decisions are ADR territory
        source = "explicit_user_statement" if _is_user(e) else "explicit_agent_statement"
        mot = RATIONALE_RE.search(text)
        out.append(Candidate(
            etype=ArtifactType.INTENTION,
            statement=text[:200],
            details={"motivation": mot.group(2).strip()[:300] if mot else ""},
            scope=_top_dirs(e.get("files")),
            source=source,
            session_id=e.get("session_id"),
            event_ids=[e["id"]],
            files=list(e.get("files") or []),
        ))
    return out


def extract_negative_knowledge(events: list[dict]) -> list[Candidate]:
    """PRD §45: 'we tried Y, it failed, do not repeat Y'."""
    out: list[Candidate] = []
    for e in events:
        if e["type"] not in ("user_instruction", "agent_response"):
            continue
        text = _clean(e.get("content"))
        if not text:
            continue
        m = NEGATIVE_RE.search(text)
        if not m:
            continue
        source = "explicit_user_statement" if _is_user(e) else "explicit_agent_statement"
        out.append(Candidate(
            etype=ArtifactType.NEGATIVE_KNOWLEDGE,
            statement=f"Evitar: {m.group(2).strip(' .')}",
            details={"kind": "rejected approach", "evidence_text": text[:300]},
            scope=_top_dirs(e.get("files")),
            source=source,
            session_id=e.get("session_id"),
            event_ids=[e["id"]],
            files=list(e.get("files") or []),
        ))
    return out


def extract_fixes(events: list[dict]) -> list[Candidate]:
    """error/test_failure followed by a resolution -> Fix with causal chain (PRD §11)."""
    fixes: list[Candidate] = []
    open_error: dict | None = None
    for e in events:
        etype = e["type"]
        content = _clean(e.get("content"))
        if etype in ERROR_EVENT_TYPES:
            open_error = e
            continue
        if open_error and etype in RESOLUTION_EVENT_TYPES and FIX_MARKER_RE.search(content or ""):
            cause_m = ROOT_CAUSE_RE.search(content)
            symptom = _clean(open_error.get("content") or "").splitlines()
            symptom = symptom[0][:180] if symptom else "unspecified error"
            root_cause = _clean(cause_m.group(2))[:200] if cause_m else "unknown (see evidence)"
            resolution = content[:300]
            commits = []
            if etype == "commit":
                commits = [str((e.get("meta") or {}).get("hash") or e["id"])]
            fixes.append(Candidate(
                etype=ArtifactType.FIX,
                statement=f"Fix: {symptom}",
                details={
                    "symptom": symptom,
                    "root_cause": root_cause,
                    "resolution": resolution,
                    "affected_files": list(e.get("files") or []),
                    "tests": [],
                },
                scope=_top_dirs(e.get("files")),
                source="code_git_evidence",
                session_id=e.get("session_id"),
                event_ids=[open_error["id"], e["id"]],
                files=list(e.get("files") or []),
                commits=commits,
            ))
            open_error = None
    return fixes


def normalize_root_cause(text: str) -> frozenset[str]:
    stop = {"the", "a", "o", "de", "da", "do", "was", "for", "com", "em", "of", "is",
            "não", "nao", "missing", "erro", "error", "unknown", "see", "evidence"}
    tokens = re.split(r"[^a-z0-9á-ú]+", text.lower())
    return frozenset(t for t in tokens if t and t not in stop and len(t) > 2)


def root_cause_similarity(a: str, b: str) -> float:
    sa, sb = normalize_root_cause(a), normalize_root_cause(b)
    if not sa or not sb:
        return 0.0
    inter = len(sa & sb)
    return inter / min(len(sa), len(sb))


# Generic statement similarity for semantic dedup (Onda 2, item 5).
_SIM_STOP = {
    "the", "and", "for", "with", "que", "por", "para", "com", "uma", "não",
    "nao", "usar", "usamos", "vamos", "decisão", "decisao", "em", "vez",
    "porque", "pois", "de", "da", "do", "no", "na",
}


def statement_tokens(text: str) -> frozenset[str]:
    tokens = re.split(r"[^a-z0-9á-úà-ùâ-ûã-õç]+", text.lower())
    return frozenset(t for t in tokens if t and t not in _SIM_STOP and len(t) > 2)


def statement_similarity(a: str, b: str) -> float:
    sa, sb = statement_tokens(a), statement_tokens(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / min(len(sa), len(sb))


@functools.lru_cache(maxsize=1)
def _semantic_model():
    """Load the optional model2vec model once per process.

    The import and model loading are isolated so the normal local fallback is
    unaffected when the optional extra is not installed or its model cannot be
    loaded.
    """
    try:
        from model2vec import StaticModel

        model_name = os.getenv("CORTEX_SEMANTIC_MODEL", "minishlab/potion-base-8M")
        return StaticModel.from_pretrained(model_name)
    except Exception:
        return None


def _model2vec_similarity(a: str, b: str) -> float | None:
    model = _semantic_model()
    if model is None:
        return None
    try:
        vectors = model.encode([a, b])
        first, second = vectors[0], vectors[1]
        sqlite_score = _sqlite_vec_similarity(first, second)
        if sqlite_score is not None:
            return sqlite_score
        dot = float(first @ second)
        norm = float((first @ first) ** 0.5 * (second @ second) ** 0.5)
        if norm <= 0:
            return None
        # Cosine is [-1, 1]; expose a conventional [0, 1] relevance score.
        return round(max(0.0, min(1.0, (dot / norm + 1.0) / 2.0)), 4)
    except Exception:
        return None


def _sqlite_vec_similarity(first, second) -> float | None:
    """Use sqlite-vec when installed; return ``None`` for graceful fallback."""
    try:
        import sqlite3

        import sqlite_vec

        first_values = first.tolist() if hasattr(first, "tolist") else list(first)
        second_values = second.tolist() if hasattr(second, "tolist") else list(second)
        conn = sqlite3.connect(":memory:")
        # sqlite-vec is a loadable SQLite extension.  Enabling extensions is
        # scoped to this in-memory connection and disabled immediately after
        # loading; no user database can load arbitrary extensions here.
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        conn.execute(
            f"CREATE VIRTUAL TABLE vectors USING vec0(embedding float[{len(first_values)}] distance_metric=cosine)"
        )
        serialize = sqlite_vec.serialize_float32
        conn.execute("INSERT INTO vectors(rowid, embedding) VALUES (?, ?)",
                     (1, serialize(first_values)))
        conn.execute("INSERT INTO vectors(rowid, embedding) VALUES (?, ?)",
                     (2, serialize(second_values)))
        row = conn.execute(
            "SELECT distance FROM vectors WHERE embedding MATCH ? AND k = 2 AND rowid = 1",
            (serialize(second_values),),
        ).fetchone()
        conn.close()
        if row is None:
            return None
        return round(max(0.0, min(1.0, 1.0 - float(row[0]))), 4)
    except Exception:
        return None


def dense_semantic_similarity(a: str, b: str) -> float:
    """Return semantic similarity, using optional local embeddings when enabled.

    ``model2vec`` is deliberately opt-in because its first use may download
    model weights.  When it is unavailable or disabled, the deterministic
    local n-gram/token implementation remains the zero-network fallback.
    """
    if not a.strip() or not b.strip():
        return 0.0
    
    # Early exit for identical strings
    if a.strip().lower() == b.strip().lower():
        return 1.0
    
    # Embeddings are opt-in: importing model2vec alone is harmless, loading a
    # model is not (weights may be fetched on first use).
    if os.getenv("CORTEX_ENABLE_DENSE_EMBEDDINGS", "").lower() in {"1", "true", "yes"}:
        embedded = _model2vec_similarity(a, b)
        if embedded is not None:
            return embedded

    # Fallback: n-gram TF-IDF cosine similarity + token similarity
    toks_a = statement_tokens(a)
    toks_b = statement_tokens(b)
    token_sim = (len(toks_a & toks_b) / min(len(toks_a), len(toks_b))) if (toks_a and toks_b) else 0.0

    def _ngrams(text: str) -> dict[str, int]:
        clean = re.sub(r"\s+", " ", text.lower().strip())
        counts: dict[str, int] = {}
        for n in (3, 4):
            for i in range(len(clean) - n + 1):
                gram = clean[i:i+n]
                counts[gram] = counts.get(gram, 0) + 1
        return counts

    vec_a = _ngrams(a)
    vec_b = _ngrams(b)
    if not vec_a or not vec_b:
        return token_sim

    common_keys = set(vec_a.keys()) & set(vec_b.keys())
    if not common_keys:
        return token_sim
    
    dot_product = sum(vec_a[k] * vec_b[k] for k in common_keys)
    norm_a = (sum(v * v for v in vec_a.values())) ** 0.5
    norm_b = (sum(v * v for v in vec_b.values())) ** 0.5
    ngram_sim = (dot_product / (norm_a * norm_b)) if (norm_a > 0 and norm_b > 0) else 0.0

    return round(max(ngram_sim, token_sim, 0.5 * ngram_sim + 0.5 * token_sim), 4)


NEGATION_TERMS = {
    "não", "nao", "never", "don't", "dont", "avoid", "evitar", "rejeitar", "rejected",
    "proibir", "desativar", "disable", "no", "sem", "without"
}
AFFIRMATIVE_TERMS = {
    "usar", "use", "adotar", "adopt", "permitir", "allow", "enable", "ativar", "prefer", "incluir"
}


def _word_boundary_re(terms: set[str]) -> re.Pattern[str]:
    # Longest-first so a multi-word/longer term (e.g. "don't") isn't shadowed
    # by a shorter one sharing a prefix.
    return re.compile(
        r"\b(?:" + "|".join(re.escape(t) for t in sorted(terms, key=len, reverse=True)) + r")\b",
        re.IGNORECASE,
    )


# Whole-word match, not `statement_tokens()`: that helper's stopword list
# (_SIM_STOP, tuned for topic-similarity) deliberately strips exactly the
# words negation detection needs ("não", "no", "usar") since they're
# near-universal function words for *that* purpose. A plain substring `in`
# check has the opposite problem (matches "no" inside "node"/"snapshot").
# Word-boundary regex gets both right: "no" alone matches, "no" inside
# "node" doesn't.
_NEGATION_RE = _word_boundary_re(NEGATION_TERMS)
_AFFIRMATIVE_RE = _word_boundary_re(AFFIRMATIVE_TERMS)

def detect_negation_conflict(text_a: str, text_b: str) -> bool:
    """Detect polar contradiction between two technical statements or decisions.

    Optimized to avoid redundant checks and early exit for obvious non-conflicts."""
    toks_a = statement_tokens(text_a)
    toks_b = statement_tokens(text_b)
    if not toks_a or not toks_b:
        return False

    common = toks_a & toks_b
    if not common:
        return False

    overlap_ratio = len(common) / min(len(toks_a), len(toks_b))
    if overlap_ratio < 0.35:
        return False

    has_neg_a = bool(_NEGATION_RE.search(text_a))
    has_neg_b = bool(_NEGATION_RE.search(text_b))

    has_aff_a = bool(_AFFIRMATIVE_RE.search(text_a))
    has_aff_b = bool(_AFFIRMATIVE_RE.search(text_b))

    # One is affirmative and one is negative on the same core subject
    return (has_neg_a and not has_neg_b and has_aff_b) or (has_neg_b and not has_neg_a and has_aff_a)
