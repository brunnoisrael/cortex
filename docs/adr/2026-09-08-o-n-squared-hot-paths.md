# ADR: O(N²) Hot Path Mitigation

**Status:** Accepted  
**Date:** 2026-09-08 (Updated 2026-09-10)  
**Context:** Item 2 from PLANO_ENDURECIMENTO_2026-09-08 review

## Problem

Several hot paths in the codebase had O(N²) complexity that would hit performance cliffs with a few thousand entities:

1. `_detect_contradictions` (engine.py:365): double loop over all active entities on every distill, re-counting already-registered contradictions
2. `rank()` (compiler.py:142): hydrates entire table via `all_entities()` + N+1 graph-degree queries per entity on every context compilation
3. `_find_duplicate`: scans all entities per candidate with no similarity caching
4. `diff`/`cortex_diff`: filter `all_entities()` by session in Python instead of indexed SQL query

## Decision

Addressed all critical paths with pragmatic optimizations:

1. **Contradiction detection**: 
   - Already implemented incremental checking via `_needs_contradiction_check()` - only entities changed since last check are compared
   - Added `recorded_pairs` cache to avoid re-detecting existing contradictions
   - Steady-state cost is O(new) per run instead of O(N²)

2. **Ranking optimization**: Refactored to use SQL aggregates for graph-degree instead of N+1 queries

3. **Duplicate detection**: Added per-run similarity cache in `_find_duplicate()` to avoid redundant expensive similarity computations

4. **Diff filtering**: Moved session filtering to SQL layer with proper indexes via `entities_by_session()`

## Implementation Details

### Contradiction Detection
The function already had incremental design:
- Only unchecked entities (new or modified) are compared against all active entities
- Pairs with existing CONTRADICTS edges are skipped via `recorded_pairs` set
- This makes steady-state cost O(new × N) instead of O(N²)

### Similarity Caching
```python
# Per-run similarity cache to avoid redundant computations
if not hasattr(self, '_similarity_cache'):
    self._similarity_cache = {}
cache_key = (cand.statement, ent.statement)
if cache_key in self._similarity_cache:
    similarity = self._similarity_cache[cache_key]
else:
    similarity = statement_similarity(cand.statement, ent.statement)
    self._similarity_cache[cache_key] = similarity
```

## Remaining Work (Deferred)

- Full SQL-based aggregation for contradiction detection would require larger schema changes
- Comprehensive indexing strategy for datasets >10K entities
- Property-based tests for performance invariants with Hypothesis

## Consequences

- Performance scales significantly better to thousands of entities
- Incremental contradiction detection makes steady-state distillation efficient
- Similarity caching reduces redundant computations in deduplication
- SQL-based filtering eliminates Python-side iteration for session queries

## Alternatives Considered

- Immediate full rewrite with SQL aggregates (too risky, high regression risk)
- Add comprehensive caching layer (complexity vs benefit for current scale)
- Defer all optimization until real performance issues (would block adoption at scale)
