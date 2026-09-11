# Optional Enhanced Integrations

- **Status**: Accepted
- **Date**: 2026-09-10

## Context

Cortex previously used small local implementations for token counting,
similarity, secret detection, TOML updates, Ollama HTTP, repository parsing,
and graph rendering. Those implementations are useful as resilient fallbacks,
but mature libraries provide stronger behavior when a project opts into them.

## Decision

The `enhanced` extra provides `tiktoken`'s already-required production token
counter plus optional integrations for `model2vec`/`sqlite-vec`,
`detect-secrets`, `tomlkit`, the OpenAI-compatible Ollama client, tree-sitter
language grammars, and pyvis.

Optional imports are lazy and failures degrade to the existing local behavior:

- dense embeddings require `CORTEX_ENABLE_DENSE_EMBEDDINGS=1`, avoiding an
  unexpected model download;
- secret scanning augments the regex redactor;
- TOMLKit preserves comments and formatting where available;
- Ollama uses the OpenAI-compatible `/v1` API and falls back to `/api/chat`;
- tree-sitter is used for supported non-Python file extensions when a grammar
  is installed;
- pyvis is used for interactive graph output and otherwise the standalone
  HTML renderer remains available.

## Consequences

The minimal install stays local-first and does not require model weights or
network services. Projects that want the enhanced integrations can install
`pip install -e ".[enhanced]"`; the existing fallbacks keep capture,
verification, and visualization operational if an optional package is absent
or incompatible.
