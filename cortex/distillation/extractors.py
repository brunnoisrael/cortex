"""Heuristic extractors: raw events -> knowledge candidates (PRD §8).

Inference hierarchy (PRD §8.3): explicit user statement > explicit agent
statement > code/git evidence > pattern > LLM inference.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from cortex.knowledge.models import (
    CONFIDENCE_BY_SOURCE,
    ArtifactType,
    Authority,
)

# ---- language patterns (PT + EN, per PRD examples) ----

DECISION_RE = re.compile(
    r"\b(vamos usar|usaremos|decidimos|decisão|escolhemos|optamos|adotaremos|"
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
    r"\b(em vez de|ao invés de|no lugar de|instead of|rather than|over)\s+([A-Za-z0-9_\-\.]{2,40})",
    re.IGNORECASE,
)
INTENTION_RE = re.compile(
    r"\b(objetivo|intent|intenção|queremos|we want|we need|precisamos|precisa permitir|"
    r"para permitir|isolar|isolate|separar|abstrair|so that the system|goal)\b",
    re.IGNORECASE,
)
NEGATIVE_RE = re.compile(
    r"\b(não usar|não utilize|não usaremos|não recomend|don't use|do not use|"
    r"avoid using|never use|rejected? because)\b\s+([A-Za-z0-9_\-\.]{2,40})",
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
            "not", "não", "missing", "erro", "error", "unknown", "see", "evidence"}
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


def dense_semantic_similarity(a: str, b: str) -> float:
    """Character n-gram (3-gram & 4-gram) subword TF-IDF cosine similarity
    plus token similarity providing dense semantic matching for paraphrases local-first.
    
    Optimized to avoid redundant calculations and early exit for edge cases."""
    if not a.strip() or not b.strip():
        return 0.0
    
    # Early exit for identical strings
    if a.strip().lower() == b.strip().lower():
        return 1.0
    
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

    # Check negation and affirmative terms in one pass
    text_a_lower = text_a.lower()
    text_b_lower = text_b.lower()
    
    has_neg_a = bool(toks_a & NEGATION_TERMS or any(n in text_a_lower for n in NEGATION_TERMS))
    has_neg_b = bool(toks_b & NEGATION_TERMS or any(n in text_b_lower for n in NEGATION_TERMS))

    has_aff_a = bool(toks_a & AFFIRMATIVE_TERMS or any(a in text_a_lower for a in AFFIRMATIVE_TERMS))
    has_aff_b = bool(toks_b & AFFIRMATIVE_TERMS or any(a in text_b_lower for a in AFFIRMATIVE_TERMS))

    # One is affirmative and one is negative on the same core subject
    return (has_neg_a and not has_neg_b and has_aff_b) or (has_neg_b and not has_neg_a and has_aff_a)

