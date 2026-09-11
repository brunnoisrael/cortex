"""Contract tests for optional enterprise integrations.

These tests do not download models, call Ollama, or require optional packages
in the minimal CI job.  They validate the activation gates, adapters, and
fallback contracts with deterministic doubles; the enhanced CI job installs
the extras and exercises the same suite.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest

from cortex.cli.app import _config_set
from cortex.distillation import extractors
from cortex.distillation.llm import OllamaDistiller
from cortex.privacy import redaction
from cortex.verification import _scan_tree_sitter


def test_dense_similarity_is_explicitly_opt_in(monkeypatch):
    calls = []

    def fake_similarity(left: str, right: str) -> float:
        calls.append((left, right))
        return 0.91

    monkeypatch.setattr(extractors, "_model2vec_similarity", fake_similarity)
    monkeypatch.delenv("CORTEX_ENABLE_DENSE_EMBEDDINGS", raising=False)
    fallback = extractors.dense_semantic_similarity("alpha", "beta")
    assert calls == []

    monkeypatch.setenv("CORTEX_ENABLE_DENSE_EMBEDDINGS", "1")
    assert extractors.dense_semantic_similarity("alpha", "beta") == 0.91
    assert calls == [("alpha", "beta")]
    assert fallback != 0.91


def test_detect_secrets_adapter_masks_only_flagged_lines(monkeypatch):
    monkeypatch.setattr(
        redaction,
        "_detect_secrets_findings",
        lambda _text: [(2, object())],
    )
    assert redaction.redact("safe\nsecret\nsafe again") == "safe\n<REDACTED_SECRET>\nsafe again"


def test_tomlkit_path_preserves_comments_when_available(tmp_path: Path):
    pytest.importorskip("tomlkit")
    config = tmp_path / "cortex.toml"
    config.write_text(
        "# project comment\n[project]\nname = \"demo\" # inline comment\n"
        "\n[context]\nmax_tokens = 2000\n",
        encoding="utf-8",
    )

    _config_set(tmp_path, "context.max_tokens", "1500")
    rendered = config.read_text(encoding="utf-8")
    assert "# project comment" in rendered
    assert "# inline comment" in rendered
    assert "max_tokens = 1500" in rendered


def test_ollama_openai_adapter_parses_json_without_network(monkeypatch):
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content='{"candidates": [{"type": "adr", "statement": "Use SQLite"}]}'))]
    )

    class Completions:
        def create(self, **_kwargs):
            return response

    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=Completions()))
    monkeypatch.setattr(OllamaDistiller, "_openai_client", lambda _self: fake_client)
    distiller = OllamaDistiller()
    result = distiller.extract([{"type": "user_instruction", "content": "Use SQLite"}])
    assert result == [{"type": "adr", "statement": "Use SQLite"}]


def test_tree_sitter_contract_scans_non_python_scope(tmp_path: Path, monkeypatch):
    source = "handleRequest();"
    target = tmp_path / "src" / "handler.js"
    target.parent.mkdir()
    target.write_text(source, encoding="utf-8")

    class Leaf:
        child_count = 0
        children: list[object] = []
        start_byte = 0
        end_byte = len("handleRequest")

    class Root:
        child_count = 1
        children = [Leaf()]

    class Parser:
        def parse(self, _source):
            return SimpleNamespace(root_node=Root())

    monkeypatch.setattr("cortex.verification._tree_sitter_parser", lambda _name: Parser())
    assert _scan_tree_sitter(tmp_path, ["src"], ["handleRequest"]) == {"handleRequest"}


def test_pyvis_adapter_is_lazy_and_escapes_graph_fields(monkeypatch, store):
    network_module = types.ModuleType("pyvis.network")

    class FakeNetwork:
        def __init__(self, **_kwargs):
            pass

        def set_options(self, _options):
            pass

        def add_node(self, *_args, **_kwargs):
            pass

        def add_edge(self, *_args, **_kwargs):
            pass

        def generate_html(self, **_kwargs):
            return "<html>pyvis</html>"

    network_module.Network = FakeNetwork
    pyvis_module = types.ModuleType("pyvis")
    pyvis_module.network = network_module
    monkeypatch.setitem(sys.modules, "pyvis", pyvis_module)
    monkeypatch.setitem(sys.modules, "pyvis.network", network_module)

    from cortex.visualizer import _generate_pyvis_html

    rendered = _generate_pyvis_html(store)
    assert rendered.startswith("<!DOCTYPE html>")
    assert "<html>pyvis</html>" in rendered
