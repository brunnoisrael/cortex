# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records for the Cortex project. ADRs document significant architectural decisions, their context, alternatives considered, and consequences.

## Recent ADRs

- [2026-09-10: CCB Benchmark Honest Signal and Adversarial Fixture](2026-09-10-ccb-benchmark-honesty.md) - Fixed self-referential benchmark and added adversarial testing
- [2026-09-10: Compiler END-Marker Budget Reservation](2026-09-10-compiler-end-marker-budget.md) - Ensures context never exceeds token budget
- [2026-09-10: MCP Listing Limits](2026-09-10-mcp-listing-limits.md) - Added limits to MCP listing tools for safety
- [2026-09-10: Connection Lifecycle Consistency](2026-09-10-connection-lifecycle-fix.md) - Completed migration to workspace_store() context manager
- [2026-09-08: cortex_remember Governance Authority Fix](2026-09-08-cortex-remember-governance-fix.md) - Fixed critical governance bug
- [2026-09-08: O(N²) Hot Path Mitigation](2026-09-08-o-n-squared-hot-paths.md) - Performance optimizations for scaling
- [2026-09-08: Service Layer Abstraction](2026-09-08-service-layer-abstraction.md) - Eliminated CLI/MCP duplication
- [2026-09-08: Timestamp Parsing Modernization](2026-09-08-timestamp-parsing-fix.md) - Modernized datetime handling
- [2026-09-08: SQLite UPSERT Migration](2026-09-08-sqlite-upsert-fix.md) - Fixed INSERT OR REPLACE antipattern
- [2026-09-08: Negation Extraction False Positive Fix](2026-09-08-negation-extraction-fix.md) - Fixed decision extraction negation handling

## ADR Format

ADRs follow the standard format:
- **Status**: Accepted, Proposed, Deprecated, or Superseded
- **Date**: When the decision was made
- **Context**: What problem motivated the decision
- **Decision**: What was decided
- **Consequences**: What results from the decision
- **Alternatives Considered**: What other options were evaluated

## Related Documentation

- [PLANO_ENDURECIMENTO_2026-09-08.md](../../PLANO_ENDURECIMENTO_2026-09-08.md) - Original hardening plan that motivated many of these ADRs
- [tests/test_review_fixes.py](../../tests/test_review_fixes.py) - Regression tests for these fixes
