# ADR: CCB Benchmark Honest Signal and Adversarial Fixture

**Status:** Accepted  
**Date:** 2026-09-10  
**Context:** Item 8 from PLANO_ENDURECIMENTO_2026-09-08 review

## Problem

The CCB (Cortex Continuity Benchmark) was self-referential: the fixture was seeded with exactly the patterns that the extractors search for, measuring the extractor against itself. This produced a misleading 8/8 score that didn't reflect real-world performance.

Additionally, `_evaluate_dynamic` in the benchmark had a vacuous pass bug: when a task had no applicable entity (empty store), it recorded a false 8/8 pass using `check(..., True, "")` instead of properly skipping the scenario.

## Decision

1. **Fixed vacuous pass bug**: Modified `_make_check` and `_score` in `benchmarks/ccb.py` to distinguish between `skip` (no applicable entity) and `pass` (correctly retrieved). Empty stores now correctly report 0/0 skipped instead of 8/8 passed.

2. **Added adversarial/paraphrased fixture**: Created `run_ccb_paraphrased()` that runs the same 8 scenarios through naturally-phrased text instead of extractor-shaped text. This is wired to `cortex benchmark --adversarial`.

3. **Updated report format**: Modified `format_report()` to handle skipped entries separately from passed/failed, making the distinction visible in output.

## Result

The tuned fixture scores 8/8, while the paraphrased one scores 4/4 with 4 skipped — proving that extraction doesn't generalize past its regex triggers. This is the honest signal the review predicted.

## Alternatives Considered

- Keep only the self-referential fixture and document its limitation
- Use real repositories for dogfood exclusively (slow, variable results)
- Replace regex extraction with LLM-based extraction (deferred to future ADR)

## Consequences

- Benchmark now provides honest signal about extraction limitations
- `--adversarial` flag enables regression testing for overfitting
- Existing `--dogfood` mode remains for real-world validation
