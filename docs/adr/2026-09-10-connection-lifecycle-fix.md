# ADR: Connection Lifecycle Consistency

**Status:** Accepted  
**Date:** 2026-09-10  
**Context:** Item 6 from PLANO_ENDURECIMENTO_2026-09-08 review

## Problem

Connection lifecycle was inconsistent across CLI commands:
- Code admitted that ~30 commands only closed the store on the happy path (cli/app.py:57-64)
- Exceptions would leak file handles
- On Windows with WAL mode, this has real consequences (locked files, inability to reopen)
- A `workspace_store()` helper existed but migration was incomplete

## Decision

Completed migration of all CLI commands to use `workspace_store()` context manager:
- Ensures `store.close()` is called in `finally` block
- Handles exceptions gracefully without resource leaks
- Updated docstring to reflect completed migration
- Only `init` and `doctor` commands retain direct store handling (intentional for their specific use cases)

## Implementation

```python
@contextmanager
def workspace_store() -> Iterator[tuple[Path, CortexConfig, KnowledgeStore]]:
    """Guarantees store.close() even when command body raises."""
    root, cfg, store = _require_workspace()
    try:
        yield root, cfg, store
    finally:
        store.close()
```

All commands now use:
```python
with workspace_store() as (_, _, store):
    # command logic
```

## Consequences

- No more file handle leaks on exceptions
- Consistent resource management across all commands
- Windows+WAL compatibility improved
- Clearer intent: any command opening a store must use this pattern

## Alternatives Considered

- Add try/finally to each command individually (verbose, error-prone)
- Use atexit handler (doesn't handle exceptions in same process)
- Keep current behavior and document limitation (unacceptable on Windows)
