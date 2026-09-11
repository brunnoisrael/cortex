# ADR: MCP Listing Limits

**Status:** Accepted  
**Date:** 2026-09-10  
**Context:** Item from PLANO_ENDURECIMENTO_2026-09-08 review

## Problem

MCP tools `cortex_intention`, `cortex_adr`, `cortex_fix`, and `cortex_correnda` returned all entities without limits. In a knowledge store with thousands of entities, this would:
- Return excessive data to the agent
- Potentially hit token limits in the MCP protocol
- Make it impossible to distinguish "no results" from "truncated results"

## Decision

Modified all MCP listing tools to accept a `limit` parameter (default 50, max 200). Results are sorted most-recent-first and return a structured response:

```json
{
  "total": 342,
  "returned": 50,
  "items": [...]
}
```

This makes truncation visible to the agent instead of silently dumping everything.

## Implementation

- Added `limit` parameter to MCP tool schemas
- Modified `list_by_type()` in storage layer to support limit/offset
- Updated MCP server handlers to return structured response
- Sorted by `created_at DESC` for most-recent-first

## Consequences

- Agents can now handle large knowledge stores safely
- Truncation is explicit, allowing agents to request more if needed
- Default of 50 provides reasonable balance between completeness and token usage
- Max of 200 prevents abuse while allowing larger batches when needed

## Alternatives Considered

- Keep unlimited listing and rely on agent token limits (unsafe)
- Use cursor-based pagination (overkill for current usage)
- Return only count without items (not useful for retrieval)
