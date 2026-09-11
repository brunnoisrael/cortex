# ADR: SQLite UPSERT Migration from INSERT OR REPLACE

**Status:** Accepted  
**Date:** 2026-09-08  
**Context:** Item 5 from PLANO_ENDURECIMENTO_2026-09-08 review

## Problem

The codebase used `INSERT OR REPLACE` as the upsert pattern (store.py:325). This is a classic SQLite antipattern:
- `REPLACE` is actually `DELETE + INSERT`
- Triggers cascades (if FKs were declared)
- Can break foreign key constraints
- Loses rowid and autoincrement behavior
- Not idempotent in the way true upsert should be

The modern SQLite upsert pattern is `INSERT ... ON CONFLICT DO UPDATE`, which has been available since 2018.

## Decision

Migrated all upsert operations from `INSERT OR REPLACE` to `INSERT ... ON CONFLICT DO UPDATE`:
- Updated entity insertion in `store.py`
- Updated FTS table sync triggers
- Used proper conflict targets (primary key or unique constraints)

## Implementation

```python
# Old
INSERT OR REPLACE INTO entities (id, ...) VALUES (?, ...)

# New
INSERT INTO entities (id, ...) VALUES (?, ...)
ON CONFLICT(id) DO UPDATE SET
    statement = excluded.statement,
    ...
```

## Consequences

- Correct upsert semantics without delete/insert cycle
- Future-proof for adding foreign key constraints
- Standard SQLite pattern recognized by the community
- No breaking changes to existing data

## Alternatives Considered

- Keep `INSERT OR REPLACE` and document limitation (technical debt)
- Use `INSERT ... ON CONFLICT IGNORE` (loses update capability)
- Add application-level check-then-insert (race condition risk)
