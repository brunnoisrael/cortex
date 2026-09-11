# ADR: Service Layer Abstraction

**Status:** Accepted  
**Date:** 2026-09-08  
**Context:** Item 3 from PLANO_ENDURECIMENTO_2026-09-08 review

## Problem

CLI and MCP duplicated orchestration logic:
- `DistillationEngine` construction with ~8 parameters appeared 3× (cli/app.py:297, mcp_server.py:238, installer.py:164)
- Phase review and "latest open session" lookup existed in near-identical pairs between app.py and mcp_server.py
- No shared abstraction for common workflows

## Decision

Created a `CortexService` (or factory) layer that both CLI and MCP facades sit on top of. This:
- Eliminates duplication of engine construction
- Centralizes common workflows (phase review, session lookup)
- Provides a single place for business logic that both interfaces share
- Makes future additions (e.g., web UI) easier

## Implementation

- Created `cortex/service.py` with `CortexService` class
- Moved engine construction, session lookup, and workflow methods into service
- Updated CLI commands to use service instead of direct engine construction
- Updated MCP server to use same service instance

## Consequences

- Reduced code duplication
- Single source of truth for business logic
- Easier to test workflows independently
- Clearer separation between interfaces (CLI/MCP) and business logic

## Alternatives Considered

- Keep duplication and accept maintenance burden (anti-pattern)
- Extract to shared utilities without formal service layer (less structured)
- Use dependency injection framework (overkill for current scope)
