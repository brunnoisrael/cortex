"""Context Continuity Benchmark — memory-quality subset (PRD §31, Onda 5).

Deterministic harness: seeds a synthetic project history, distills it, and
evaluates whether the compiled context answers the 8 task types of §31.4.
No external agent needed — this measures memory quality (recall precision,
false memory rate, provenance coverage), the controllable half of CCG.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from cortex.capture.recorder import capture_event
from cortex.compiler.compiler import CompileInput, compile_context
from cortex.config import write_default_config
from cortex.distillation.engine import DistillationEngine
from cortex.distillation.review import build_session_review
from cortex.knowledge.models import ArtifactType, Status
from cortex.storage.store import KnowledgeStore
from cortex.workspace import ensure_cortex_dir


def _seed_history(store: KnowledgeStore) -> None:
    for sid in ("h1", "h2", "h3", "h4", "h5"):
        store.ensure_session(sid, host="ccb")

    capture_event(store, {"type": "user_instruction", "session_id": "h1",
                          "content": "Decidimos PostgreSQL em vez de MongoDB porque precisamos de transações ACID.",
                          "files": ["src/db/schema.sql"]})
    capture_event(store, {"type": "user_instruction", "session_id": "h1",
                          "content": "Não usar DynamoDB neste domínio, foi rejeitado no ADR por lock-in.",
                          "files": ["src/db/"]})
    capture_event(store, {"type": "session_start", "session_id": "h2",
                          "content": "Isolar auth via middleware para permitir troca de provider sem tocar nos handlers",
                          "files": ["src/auth/"]})
    for sid, err in (("h2", "TypeError: NoneType payload"), ("h3", "TypeError: payload malformed")):
        capture_event(store, {"type": "error", "session_id": sid, "content": err,
                              "files": ["src/handlers/webhook_handler.py"]})
        capture_event(store, {"type": "agent_response", "session_id": sid,
                              "content": "Fix: validação Pydantic porque payload externo não era validado",
                              "files": ["src/handlers/webhook_handler.py"]})
    capture_event(store, {"type": "user_instruction", "session_id": "h4",
                          "content": "Ficou pendente: estratégia de cache para o endpoint de pricing",
                          "files": ["src/pricing/"]})
    capture_event(store, {"type": "user_instruction", "session_id": "h5",
                          "content": "Decidimos migrar para Aurora Postgres em vez de PostgreSQL puro, porque gerenciado reduz operação.",
                          "files": ["src/db/"]})

    engine = DistillationEngine(store)
    engine.distill_all()
    build_session_review(store, "h4")

    adrs = sorted(store.list_by_type(ArtifactType.ADR), key=lambda e: e.id)
    if len(adrs) >= 2:
        store.supersede(adrs[0].id, adrs[-1].id)  # Aurora supersedes plain PostgreSQL
    from cortex.knowledge.models import Authority
    correndas = store.list_by_type(ArtifactType.CORRENDA)
    if correndas:
        store.set_status(correndas[0].id, Status.ACTIVE, authority=Authority.HUMAN_CONFIRMED)


def _leak_count(store: KnowledgeStore, context_text: str) -> int:
    """False memory = a superseded/stale artifact leaking into the compiled
    context (id or decision text) — never acceptable (PRD §17). Shared by
    both evaluators (fixture and dogfooding): identical rule, only the task
    logic that decides *what* to query differs between them."""
    leaks = 0
    for e in store.all_entities():
        if e.is_current and not e.freshness.stale:
            continue
        signals = [e.id, e.statement]
        decision = e.details.get("decision") or ""
        if decision:
            signals.append(decision)
        if context_text and any(s and s in context_text for s in signals):
            leaks += 1
    return leaks


def _make_check(store: KnowledgeStore, results: dict[str, dict]):
    def check(name: str, ok: bool, context_text: str = "") -> None:
        results[name] = {"pass": bool(ok), "false_memories": _leak_count(store, context_text)}
    return check


def _score(store: KnowledgeStore, results: dict[str, dict]) -> dict:
    """Shared final aggregation (8 task results -> pass rate, false-memory
    rate, provenance coverage) for both evaluators."""
    all_artifacts = [e for e in store.all_entities()
                     if e.type in (ArtifactType.ADR, ArtifactType.FIX,
                                   ArtifactType.CORRENDA, ArtifactType.INTENTION,
                                   ArtifactType.NEGATIVE_KNOWLEDGE)]
    prov_covered = [e for e in all_artifacts
                    if e.provenance.source_events or e.provenance.source_entities
                    or e.provenance.source_commits]
    tasks_passed = sum(1 for r in results.values() if r["pass"])
    total_selected = max(1, len(results))
    return {
        "tasks_passed": tasks_passed,
        "tasks_total": len(results),
        "per_task": {k: {"pass": v["pass"], "false_memories": v["false_memories"]}
                     for k, v in results.items()},
        "false_memory_rate": round(
            sum(r["false_memories"] for r in results.values()) / total_selected, 3),
        "provenance_coverage": round(len(prov_covered) / max(1, len(all_artifacts)), 3),
    }


def run_ccb(root: Path | None = None) -> dict:
    tmp = None
    if root is None:
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
    (root / "src" / "handlers").mkdir(parents=True, exist_ok=True)
    (root / "src" / "db").mkdir(parents=True, exist_ok=True)
    (root / "src" / "auth").mkdir(parents=True, exist_ok=True)
    write_default_config(root, "ccb-fixture")
    ensure_cortex_dir(root)
    store = KnowledgeStore(root / ".cortex" / "cortex.db")
    try:
        _seed_history(store)
        return _evaluate(store)
    finally:
        store.close()
        if tmp:
            tmp.cleanup()


def run_ccb_on_store(store: KnowledgeStore) -> dict:
    """Run CCB evaluation dynamically on a real initialized store (dogfooding, Onda 8)."""
    return _evaluate_dynamic(store)


def _evaluate_dynamic(store: KnowledgeStore) -> dict:
    """Dynamic CCB evaluation for real project stores (Onda 8 dogfooding):
    generic task logic that adapts to whatever entities actually exist,
    unlike _evaluate()'s fixed expectations against the synthetic fixture."""
    def ctx(query, files):
        return compile_context(store, CompileInput(query=query, files=files))

    results: dict[str, dict] = {}
    check = _make_check(store, results)

    adrs = [e for e in store.list_by_type(ArtifactType.ADR) if e.is_current]
    correndas = store.list_by_type(ArtifactType.CORRENDA)
    active_cor = [e for e in correndas if e.status == Status.ACTIVE]
    intentions = [e for e in store.list_by_type(ArtifactType.INTENTION) if e.is_current]
    fixes = store.list_by_type(ArtifactType.FIX)

    # 1. Explain why a decision exists
    if adrs:
        adr = adrs[0]
        c = ctx(adr.statement[:30], adr.scope)
        check("1_explain_why_decision", adr.statement[:25] in c or adr.id in c, c)
    else:
        check("1_explain_why_decision", True, "")

    # 2. Avoid a previously rejected solution
    adrs_with_rejected = [a for a in adrs if a.details.get("alternatives_rejected")]
    if adrs_with_rejected:
        adr = adrs_with_rejected[0]
        c = ctx(adr.statement[:30], adr.scope)
        rej = adr.details.get("alternatives_rejected", [])[0]
        check("2_avoid_rejected_solution", rej in c or "rejected" in c, c)
    else:
        check("2_avoid_rejected_solution", True, "")

    # 3. Diagnose a recurring bug
    if fixes or correndas:
        target = (fixes + correndas)[0]
        c = ctx(target.statement[:30], target.scope)
        check("3_diagnose_recurring_bug", target.id in c or target.statement[:20] in c, c)
    else:
        check("3_diagnose_recurring_bug", True, "")

    # 4. Apply a learned project rule
    if active_cor:
        cor = active_cor[0]
        c = ctx(cor.statement[:30], cor.scope)
        check("4_apply_learned_rule", cor.statement[:25] in c or cor.id in c, c)
    else:
        check("4_apply_learned_rule", True, "")

    # 5. Find unresolved work from a previous session
    reviews = store.list_by_type(ArtifactType.REVIEW)
    if reviews or intentions:
        c = ctx("unresolved work pendente", [])
        check("5_find_unresolved_work", len(c) > 0, c)
    else:
        check("5_find_unresolved_work", True, "")

    # 6. Respect a superseded decision
    superseded = [e for e in store.all_entities() if e.status == Status.SUPERSEDED]
    if superseded:
        old = superseded[0]
        c = ctx(old.statement[:30], old.scope)
        check("6_respect_superseded", old.statement not in c, c)
    else:
        check("6_respect_superseded", True, "")

    # 7. Continue an interrupted implementation
    if intentions:
        intent = intentions[0]
        c = ctx(intent.statement[:30], intent.scope)
        check("7_continue_interrupted", intent.statement[:20] in c or intent.id in c, c)
    else:
        check("7_continue_interrupted", True, "")

    # 8. Locate evidence behind a historical rule
    if correndas:
        check("8_locate_evidence", all(e.provenance.source_entities or e.provenance.source_events for e in correndas), "")
    else:
        check("8_locate_evidence", True, "")

    return _score(store, results)


def _evaluate(store: KnowledgeStore) -> dict:
    """Fixed evaluation against the synthetic fixture seeded by
    _seed_history(): fixed queries and fixed expected keywords, since the
    fixture's content is known in advance (unlike _evaluate_dynamic)."""
    def ctx(query, files):
        return compile_context(store, CompileInput(query=query, files=files))

    results: dict[str, dict] = {}
    check = _make_check(store, results)

    # 1. Explain why a decision exists
    c = ctx("banco de dados transações", ["src/db/"])
    check("1_explain_why_decision",
          "Aurora Postgres" in c or "PostgreSQL" in c, c)

    # 2. Avoid a previously rejected solution
    c = ctx("escolher banco de dados documento", ["src/db/"])
    check("2_avoid_rejected_solution", "MongoDB" in c, c)

    # 3. Diagnose a recurring bug
    c = ctx("erro de payload no webhook", ["src/handlers/webhook_handler.py"])
    check("3_diagnose_recurring_bug", "CORRENDA" in c.upper(), c)

    # 4. Apply a learned project rule
    cor = store.list_by_type(ArtifactType.CORRENDA)
    active_cor = [e for e in cor if e.status == Status.ACTIVE]
    c = ctx("novo handler de webhook", ["src/handlers/webhook_v2.py"])
    check("4_apply_learned_rule",
          bool(active_cor) and active_cor[0].statement[:30] in c, c)

    # 5. Find unresolved work from a previous session
    c = ctx("o que ficou pendente no pricing", ["src/pricing/"])
    check("5_find_unresolved_work", "pendente" in c.lower() or "pricing" in c.lower(), c)

    # 6. Respect a superseded decision
    adrs = sorted(store.list_by_type(ArtifactType.ADR), key=lambda e: e.id)
    if adrs:
        old, new = adrs[0], adrs[-1]
        c = ctx("banco de dados", ["src/db/"])
        old_decision = old.details.get("decision") or ""
        superseded_absent = old.statement not in c and old_decision not in c
        check("6_respect_superseded",
              superseded_absent and (new.details.get("decision") or "") in c, c)
    else:
        check("6_respect_superseded", False, "")

    # 7. Continue an interrupted implementation
    intentions = store.list_by_type(ArtifactType.INTENTION)
    c = ctx("continuar o trabalho de auth middleware", ["src/auth/middleware.py"])
    check("7_continue_interrupted",
          any(i.statement[:25] in c for i in intentions), c)

    # 8. Locate evidence behind a historical rule
    correndas = store.list_by_type(ArtifactType.CORRENDA)
    check("8_locate_evidence",
          bool(correndas) and all(
              e.provenance.source_entities or e.provenance.source_events
              for e in correndas), "")

    return _score(store, results)


def format_report(report: dict) -> str:
    lines = ["CCB (memory-quality subset) — PRD §31.4", "=" * 46]
    for name, r in report["per_task"].items():
        mark = "PASS" if r["pass"] else "FAIL"
        lines.append(f"[{mark}] {name}  (false memories: {r['false_memories']})")
    lines.append("-" * 46)
    lines.append(f"tasks: {report['tasks_passed']}/{report['tasks_total']}")
    lines.append(f"false_memory_rate: {report['false_memory_rate']:.1%}  (goal < 5%)")
    lines.append(f"provenance_coverage: {report['provenance_coverage']:.1%}  (goal > 95%)")
    return "\n".join(lines)
