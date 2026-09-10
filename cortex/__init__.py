"""Cortex — local-first engineering knowledge compiler for AI coding agents.

Turns coding-agent sessions into provenance-backed project knowledge
(Intention, ADR, Fix, Correnda, Review) and compiles the right knowledge
back into future sessions.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    # Single source of truth: pyproject.toml's [project] version, read back
    # through the installed distribution metadata instead of a second
    # hardcoded literal here that inevitably drifts out of sync with it.
    __version__ = version("cortex-knowledge")
except PackageNotFoundError:  # running from source without an install
    __version__ = "0.0.0+unknown"

PRINCIPLES = (
    "local-first",
    "provenance-first",
    "engineering-first",
)
