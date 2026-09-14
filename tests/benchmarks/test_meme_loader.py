from pathlib import Path

from cortex.benchmarks.loaders.meme import load_meme


def test_meme_loader_does_not_treat_run_manifest_as_meme_data():
    assert load_meme(Path("cortex/benchmarks/corpora/manifests/mvp.json")) == []
