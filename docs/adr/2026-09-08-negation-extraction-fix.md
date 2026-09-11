# ADR: Negation Extraction False Positive Fix

**Status:** Accepted  
**Date:** 2026-09-08  
**Context:** Item 7 from PLANO_ENDURECIMENTO_2026-09-08 review

## Problem

The `extract_decisions` function had a structural false positive:
- It matched `DECISION_RE` patterns without checking for negation first
- Phrases like "não vamos usar DynamoDB" or "we decided not to use MongoDB" generated ADR candidates *affirming* the rejected technology
- The `NEGATIVE_RE` pattern existed but ran in a separate independent extractor
- This is inherent fragility of regex-based PT/EN extraction

## Decision

Modified extraction pipeline to check negation before decision extraction:
- `NEGATIVE_RE` check now runs before `DECISION_RE` matching
- If negation is detected, the entity is marked as a rejection with proper negative knowledge semantics
- Decision extraction only proceeds when no negation is present
- Updated entity details to capture both the decision and what was rejected

## Implementation

```python
# Check negation first
if NEGATIVE_RE.search(text):
    # Extract what was rejected and mark as negative knowledge
    rejected = extract_rejected_technology(text)
    return create_negative_intention(rejected, ...)
    
# Only then check for positive decisions
if DECISION_RE.search(text):
    return extract_positive_decision(text, ...)
```

## Consequences

- Eliminates false positives where rejections are misinterpreted as affirmations
- Better captures negative knowledge ("we tried X and it failed")
- Still limited by regex approach — `cortex_emit` remains the robust path for structured knowledge
- LLM-based extraction with function calling remains future improvement

## Alternatives Considered

- Keep current behavior and document limitation (unacceptable for core product)
- Move to LLM-based extraction entirely (removes offline capability)
- Strengthen regex patterns with more negation cases (arms race with language complexity)
