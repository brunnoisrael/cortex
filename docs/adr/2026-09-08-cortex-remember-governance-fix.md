# ADR: cortex_remember Governance Authority Fix

**Status:** Accepted  
**Date:** 2026-09-08  
**Context:** Item 1 from PLANO_ENDURECIMENTO_2026-09-08 review

## Problem

The `cortex_remember` MCP tool recorded any call with `authority=HUMAN_CONFIRMED`, `confidence=0.95`, and `confirmed_by_human=True`. Since this tool is called by the agent (not the human), this allowed any agent to mint knowledge at the top of the authority hierarchy — contradicting the product's core thesis that "learned rules never become law on their own."

The `cortex_emit` tool correctly used `AGENT_INFERRED` and `PROPOSED` status, but `cortex_remember` bypassed this governance discipline.

## Decision

Modified `cortex_remember` in `cortex/server/mcp_server.py:145` to use the same authority discipline as `cortex_emit`:
- Authority: `AGENT_INFERRED`
- Status: `PROPOSED` (never `ACTIVE`)
- Confidence: calculated from agent-provided confidence (capped at 0.9)
- `confirmed_by_human`: always `False`

## Consequences

- Agents can no longer mint high-authority knowledge directly
- All agent-originated knowledge requires human confirmation to become `ACTIVE`
- Preserves the governance hierarchy: HUMAN_CONFIRMED > AGENT_INFERRED
- Aligns with README promise: "regra aprendida nunca vira lei sozinha"

## Alternatives Considered

- Remove `cortex_remember` entirely (breaks existing usage)
- Add explicit confirmation step to `cortex_remember` (UX friction)
- Keep current behavior and document as feature (contradicts product thesis)
