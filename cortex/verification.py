"""Repository verification (PRD §47, Onda 4 item 12).

Honest verification: a memory is promoted to `repository_verified` only when
cited symbols/patterns are actually found in the files under its scope.
Missing scope paths flag staleness. No evidence -> no promotion.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

from cortex.knowledge.models import Authority, Entity, _utcnow
from cortex.storage.store import KnowledgeStore

# words that are too generic to count as evidence when found in code
STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "porque", "por", "para",
    "com", "que", "uma", "uns", "não", "nao", "sim", "usar", "usamos",
    "vamos", "decisão", "decisao", "fix", "erro", "error", "em",
    "vez", "como", "onde", "qual", "quando", "precisamos", "precisa",
    "sendo", "each", "must", "should", "will", "make",
}

IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")

MAX_FILES = 200
MAX_BYTES = 512 * 1024


def evidence_tokens(entity: Entity) -> list[str]:
    text = entity.statement + " " + " ".join(
        v for v in entity.details.values() if isinstance(v, str)
    )
    tokens = [t for t in IDENT_RE.findall(text) if t.lower() not in STOPWORDS]
    return tokens[:8]


def _scan_ast(root: Path, scope: list[str], tokens: list[str]) -> set[str]:
    """Onda 7: AST Verification for Python targets — structural proof (Tier 0)."""
    found_ast: set[str] = set()
    for s in scope:
        base = root / s
        if base.is_file() and base.suffix == ".py":
            files = [base]
        elif base.is_dir():
            files = [p for p in base.rglob("*.py") if p.is_file()]
        else:
            parent_seg = s.split("/")[0]
            files = [p for p in (root / parent_seg).rglob("*.py")
                     if p.is_file() and s in p.as_posix()]
        
        for f in files:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                tree = ast.parse(content, filename=str(f))
            except Exception:
                continue
            
            ast_names: set[str] = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        ast_names.add(alias.name.split(".")[0])
                        if alias.asname:
                            ast_names.add(alias.asname)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        ast_names.add(node.module.split(".")[0])
                    for alias in node.names:
                        ast_names.add(alias.name)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    ast_names.add(node.name)
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        ast_names.add(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        ast_names.add(node.func.attr)
                        
            ast_names_lower = {n.lower() for n in ast_names}
            for tok in tokens:
                if tok in ast_names or tok.lower() in ast_names_lower:
                    found_ast.add(tok)
    return found_ast


def _scan(root: Path, scope: list[str], tokens: list[str]) -> set[str]:
    found: set[str] = set()
    budget = MAX_BYTES
    scanned = 0
    for s in scope:
        base = root / s
        if base.is_file():
            files = [base]
        elif base.is_dir():
            files = [p for p in base.rglob("*") if p.is_file()]
        else:
            # scope may be a prefix like src/db matching src/db/schema.sql
            files = [p for p in (root / s.split("/")[0]).rglob("*")
                     if p.is_file() and s in p.as_posix()]
        for f in files:
            if scanned >= MAX_FILES or budget <= 0:
                return found
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            scanned += 1
            budget -= len(content)
            low = content.lower()
            for tok in tokens:
                if tok in content or tok.lower() in low:
                    found.add(tok)
    return found


def verify_entity(store: KnowledgeStore, root: Path, entity: Entity) -> dict:
    """Verify one entity against the repository. Mutates the store only when
    there is real evidence (verified) or the scope is gone (stale)."""
    if not entity.scope:
        return {"status": "unverified",
                "detail": "no scope to verify against", "authority": entity.authority.value}

    def _scope_exists(s: str) -> bool:
        full = root / s
        if full.exists():
            return True
        # scope may be a prefix like "src/db" matching "src/db/schema.sql"
        parent = root / s.split("/")[0]
        if not parent.exists():
            return False
        return any(s in p.as_posix() for p in parent.rglob("*"))

    missing = [s for s in entity.scope if not _scope_exists(s)]
    if missing:
        entity.freshness.stale = True
        entity.updated_at = _utcnow()
        store.upsert(entity)
        return {"status": "stale", "detail": f"scope paths missing: {missing}",
                "authority": entity.authority.value}

    tokens = evidence_tokens(entity)
    found_ast = _scan_ast(root, entity.scope, tokens)
    found = found_ast or _scan(root, entity.scope, tokens)
    
    if tokens and found:
        store.set_status(entity.id, entity.status, authority=Authority.REPOSITORY_VERIFIED)
        ent = store.get(entity.id)
        ent.freshness.last_verified_at = _utcnow()
        ent.freshness.verification_source = "ast" if found_ast else "repository"
        ent.freshness.stale = False
        store.upsert(ent)
        verifier_type = "AST Tier 0" if found_ast else "Grep text"
        return {"status": "verified",
                "detail": f"symbols found in code ({verifier_type}): {sorted(found)[:5]}",
                "authority": Authority.REPOSITORY_VERIFIED.value,
                "verification_source": ent.freshness.verification_source}

    return {"status": "unverified",
            "detail": "no cited symbols found in scope files (authority unchanged)",
            "authority": entity.authority.value}

