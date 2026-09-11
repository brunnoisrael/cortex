# ADR: Timestamp Parsing Modernization

**Status:** Accepted  
**Date:** 2026-09-08  
**Context:** Item 4 from PLANO_ENDURECIMENTO_2026-09-08 review

## Problem

Timestamps were handled as strings with manual parsing:
- `_utcnow()` used `time.strftime` with a fixed format
- `_days_since` used `strptime` with an exact format
- Any ISO timestamp with offset or milliseconds became "unparsed" and was silently skipped
- Not compatible with modern Python 3.11+ datetime handling

## Decision

Standardized on Python 3.11+ datetime APIs:
- Use `datetime.now(UTC).isoformat()` for generation
- Use `datetime.fromisoformat()` for parsing (handles 'Z' suffix and offsets)
- Created single helper `_utcnow()` and `_parse_timestamp()` for consistency
- Removed fragile manual string format handling

## Implementation

```python
from datetime import datetime, UTC

def _utcnow() -> str:
    return datetime.now(UTC).isoformat()

def _parse_timestamp(ts: str) -> datetime | None:
    try:
        return datetime.fromisoformat(ts.replace('Z', '+00:00'))
    except ValueError:
        return None
```

## Consequences

- Robust timestamp handling compatible with ISO 8601 standard
- Handles offsets and milliseconds correctly
- Single source of truth for timestamp operations
- Failed parsing is explicit (returns None) rather than silent skip

## Alternatives Considered

- Keep manual parsing with more format strings (fragile)
- Use third-party library like dateutil (adds dependency)
- Store as Unix timestamps (loses human readability)
