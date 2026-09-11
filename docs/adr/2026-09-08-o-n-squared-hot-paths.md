# ADR: O(N²) Hot Path Mitigation

**Status:** Partially Accepted  
**Date:** 2026-09-08  
**Context:** Item 2 from PLANO_ENDURECIMENTO_2026-09-08 review

## Problem

Several hot paths in the codebase had O(N²) complexity that would hit performance cliffs with a few thousand entities:

1. `_detect_contradictions` (engine.py:365): double loop over all active entities on every distill, re-counting already-registered contradictions
2. `rank()` (compiler.py:142): hydrates entire table via `all_entities()` + N+1 graph-degree queries per entity on every context compilation
3. `_find_duplicate`: scans all entities per candidate with a "similarity cache" that never repeats within a call (dead optimization)
4. `diff`/`cortex_diff`: filter `all_entities()` by session in Python instead of indexed SQL query

## Decision

Addressed the most critical paths:

1. **Contradiction detection**: Added caching of previously-detected contradictions to avoid re-counting on successive runs
2. **Ranking optimization**: Refactored to use SQL aggregates for graph-degree instead of N+1 queries
3. **Diff filtering**: Moved session filtering to SQL layer with proper indexes

## Remaining Work

- Full SQL-based aggregation for contradiction detection (deferred)
- Comprehensive indexing strategy for larger datasets (deferred)
- Property-based tests for performance invariants (deferred)

## Consequences

- Performance scales better to thousands of entities
- Some optimizations are partial; full O(N²) elimination requires larger refactoring
- Added technical debt markers for future optimization rounds

## Alternatives Considered

- Immediate full rewrite of all hot paths (too risky, high regression risk)
- Add caching layer at application level (complexity vs benefit)
- Defer all optimization until real performance issues (would block adoption)
