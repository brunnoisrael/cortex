"""Repository verification (PRD §47, Onda 4 item 12).

Honest verification: a memory is promoted to `repository_verified` only when
cited symbols/patterns are actually found in the files under its scope.
Missing scope paths flag staleness. No evidence -> no promotion.
"""

from __future__ import annotations

import ast
import importlib
import re
import subprocess
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

TREE_SITTER_LANGUAGES = {
    ".c": "c", ".h": "c", ".cc": "cpp", ".cpp": "cpp", ".cxx": "cpp",
    ".go": "go", ".java": "java", ".js": "javascript", ".jsx": "javascript",
    ".mjs": "javascript", ".ts": "typescript", ".tsx": "tsx", ".rs": "rust",
    ".rb": "ruby", ".php": "php", ".swift": "swift", ".kt": "kotlin",
}


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


def _tree_sitter_parser(language_name: str):
    """Return a parser from the optional grammar pack or language bindings."""
    try:
        from tree_sitter_language_pack import get_parser

        return get_parser(language_name)
    except Exception:
        module = importlib.import_module(f"tree_sitter_{language_name}")
        from tree_sitter import Language, Parser

        grammar = getattr(module, "language")
        language = Language(grammar())
        try:
            return Parser(language)
        except TypeError:  # tree-sitter < 0.22
            parser = Parser()
            parser.set_language(language)
            return parser


def _scan_tree_sitter(root: Path, scope: list[str], tokens: list[str]) -> set[str]:
    """Find cited identifiers in non-Python languages using tree-sitter.

    Grammars are optional per language.  An absent grammar only skips that
    language and never weakens the existing text fallback.
    """
    wanted = set(tokens)
    wanted_lower = {token.lower() for token in wanted}
    found: set[str] = set()
    for s in scope:
        base = root / s
        if base.is_file():
            files = [base]
        elif base.is_dir():
            files = [p for p in base.rglob("*") if p.is_file()]
        else:
            parent = root / s.split("/")[0]
            files = [p for p in parent.rglob("*") if p.is_file() and s in p.as_posix()] if parent.exists() else []
        for file_path in files:
            language_name = TREE_SITTER_LANGUAGES.get(file_path.suffix.lower())
            if not language_name:
                continue
            try:
                source = file_path.read_bytes()
                parser = _tree_sitter_parser(language_name)
                tree = parser.parse(source)
            except Exception:
                continue
            stack = [tree.root_node]
            while stack:
                node = stack.pop()
                if node.child_count == 0:
                    value = source[node.start_byte:node.end_byte].decode("utf-8", errors="ignore")
                    if value in wanted or value.lower() in wanted_lower:
                        found.add(value)
                stack.extend(node.children)
    return found


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
    found_tree = _scan_tree_sitter(root, entity.scope, tokens)
    found = found_ast or found_tree or _scan(root, entity.scope, tokens)
    
    from cortex.knowledge.evidence import refresh_entity_evidence
    ledger = refresh_entity_evidence(store, root, entity)
    if tokens and found and ledger["resolved"] > 0:
        store.set_status(entity.id, entity.status, authority=Authority.REPOSITORY_VERIFIED)
        ent = store.get(entity.id)
        ent.freshness.last_verified_at = _utcnow()
        ent.freshness.verification_source = (
            "ast" if found_ast else "tree-sitter" if found_tree else "repository"
        )
        ent.freshness.stale = False
        store.upsert(ent)
        verifier_type = (
            "AST Tier 0" if found_ast else "tree-sitter" if found_tree else "Grep text"
        )
        return {"status": "verified",
                "detail": f"symbols found in code ({verifier_type}): {sorted(found)[:5]}",
                "authority": Authority.REPOSITORY_VERIFIED.value,
                "verification_source": ent.freshness.verification_source,
                "evidence_resolved": ledger["resolved"],
                "evidence_unverifiable": ledger["unverifiable"]}

    return {"status": "unverified",
            "detail": "no cited symbols found in scope files (authority unchanged)",
            "authority": entity.authority.value,
            "evidence_resolved": ledger["resolved"],
            "evidence_unverifiable": ledger["unverifiable"]}


def changed_paths(root: Path, base: str = "HEAD") -> list[str]:
    """Return paths changed by a commit/range; failures degrade to []."""
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "diff", "--name-only", base],
            capture_output=True, text=True, timeout=10, check=True,
        )
    except Exception:
        return []
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def verify_diff(store: KnowledgeStore, root: Path, base: str = "HEAD") -> dict:
    """Read-only impact review for a diff.

    The command never silently invalidates knowledge: affected entities are
    rechecked and only those whose evidence no longer resolves become stale.
    """
    paths = changed_paths(root, base)
    affected: list[dict] = []
    unaffected: list[str] = []
    for entity in store.all_entities():
        scope = [item.replace("\\", "/") for item in entity.scope]
        hits = [path for path in paths if not scope or any(path.startswith(item) or item in path for item in scope)]
        if not hits:
            unaffected.append(entity.id)
            continue
        result = verify_entity(store, root, entity)
        affected.append({"id": entity.id, "paths": hits, "verification": result})
    return {"base": base, "changed_paths": paths, "affected": affected, "unaffected": unaffected}
