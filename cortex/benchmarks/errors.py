"""Typed failures for the versioned benchmark harness.

Benchmark errors are deliberately not converted to metric zeroes.  The runner
serialises them separately so a broken adapter cannot look like a poor result.
"""

from __future__ import annotations


class BenchmarkError(Exception):
    """Base class for errors that invalidate a benchmark case or run."""


class LeakageError(BenchmarkError):
    """The adapter was exposed to data outside the case cutoff."""


class SchemaError(BenchmarkError):
    """A benchmark instance, result, or manifest is invalid."""


class BenchmarkSpecAmbiguity(BenchmarkError):
    """The frozen benchmark specification is ambiguous for the input."""


AmbiguityError = BenchmarkSpecAmbiguity


class AdapterTimeoutError(BenchmarkError):
    """An adapter exceeded the configured deterministic timeout."""
