# ADR: Compiler END-Marker Budget Reservation

**Status:** Accepted  
**Date:** 2026-09-10  
**Context:** Item from PLANO_ENDURECIMENTO_2026-09-08 review

## Problem

The Context Compiler appended the `<!-- END CORTEX CONTEXT -->` marker unconditionally in `compiler.py:345`. If the token budget was already exhausted by the compiled content, this marker would be appended anyway, potentially exceeding the advertised budget.

## Decision

Modified the `fits()` function in `compiler.py` to reserve the token cost of the END marker before deciding whether to include a candidate entity. The marker is now only appended if the budget permits it.

## Implementation

```python
# Reserve space for END marker in budget check
END_MARKER_TOKENS = estimate_tokens("<!-- END CORTEX CONTEXT -->")
available_budget = budget - END_MARKER_TOKENS
# ... entity selection happens against available_budget
```

## Consequences

- Context never exceeds the advertised token budget
- Edge case where budget is too small for even the marker is handled gracefully
- Property-based test recommended with Hypothesis to formalize this invariant

## Alternatives Considered

- Truncate content to make room for marker (could break partial sentences)
- Remove marker when budget is tight (loses useful delimiter)
- Raise error when budget exceeded (breaks "never block agent" principle)
