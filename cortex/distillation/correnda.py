"""Correnda generation: repeated root causes -> proposed engineering rules (PRD §12).

A Correnda is never born active (ADR-C3): automatic promotion stops at `proposed`.
Generation considers frequency, similarity, scope consistency and evidence
quality — not bare occurrence count (PRD §12.4).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from cortex.distillation.extractors import root_cause_similarity
from cortex.knowledge.models import Entity


@dataclass
class CorrendaGroup:
    root_cause: str
    fixes: list[Entity] = field(default_factory=list)

    @property
    def confidence(self) -> float:
        """PRD §12.4: frequency + similarity + scope consistency — not bare count.
        Two identical fixes in the same scope land ~0.85; loose groups score lower."""
        base = min(0.80, 0.55 + 0.10 * len(self.fixes))
        sim = self.avg_similarity()
        scope_c = 1.0 if self.scope_consistency() else 0.88
        return round(min(0.85, (base + 0.15 * sim) * scope_c), 2)

    def avg_similarity(self) -> float:
        from itertools import combinations
        pairs = list(combinations(self.fixes, 2))
        if not pairs:
            return 1.0
        total = sum(
            root_cause_similarity(a.details.get("root_cause", ""),
                                  b.details.get("root_cause", ""))
            for a, b in pairs
        )
        return total / len(pairs)

    def scope_consistency(self) -> bool:
        scopes = [set(_scope_of(f)) for f in self.fixes if _scope_of(f)]
        return bool(scopes) and bool(set.intersection(*scopes))


def _scope_of(fix: Entity) -> list[str]:
    return [p for p in fix.scope if p]


def group_recurring_root_causes(fixes: list[Entity], min_similarity: float = 0.6,
                                min_evidence: int = 2,
                                already_used: set[str] | None = None) -> list[CorrendaGroup]:
    """Group fixes whose root causes are similar; only groups with enough
    evidence become candidates. Fixes already serving as evidence for an
    existing correnda are excluded (no double counting)."""
    already_used = already_used or set()
    pending = [f for f in fixes if f.id not in already_used]
    groups: list[CorrendaGroup] = []
    for fix in pending:
        rc = fix.details.get("root_cause", "")
        if not rc or rc.startswith("unknown"):
            continue
        placed = False
        for g in groups:
            if root_cause_similarity(g.root_cause, rc) >= min_similarity:
                g.fixes.append(fix)
                placed = True
                break
        if not placed:
            groups.append(CorrendaGroup(root_cause=rc, fixes=[fix]))
    return [g for g in groups if len(g.fixes) >= min_evidence]


def correnda_scope(group: CorrendaGroup) -> list[str]:
    """Scope consistency: intersect fix scopes; fall back to union (PRD §12.4)."""
    scopes = [set(_scope_of(f)) for f in group.fixes if _scope_of(f)]
    if not scopes:
        return []
    common = set.intersection(*scopes)
    if common:
        return sorted(common)
    return sorted(set.union(*scopes))


def correnda_statement(group: CorrendaGroup) -> str:
    rc = group.root_cause.strip().rstrip(".")
    # Turn the observed cause into a prevention rule
    return f"Prevenir recorrência: {rc}"


def evidence_edges(group: CorrendaGroup) -> list[tuple[str, str]]:
    """Fix ──GENERATED──> Correnda (PRD §14.4)."""
    return [(f.id, "GENERATED") for f in group.fixes]
