from __future__ import annotations

from .bm25 import BM25Adapter


class CortexAdapter(BM25Adapter):
    """Offline Cortex-shaped adapter for the MVP.

    The lexical implementation is intentionally conservative: it provides a
    complete envelope and provenance trace while the real store-backed
    distillation integration is added in the later benchmark waves.
    """

    name = "cortex"

    def __init__(self, *, disable_supersession=False, disable_contradiction_penalty=False,
                 disable_authority=False, disable_dense=False, disable_graph_density=False,
                 disable_evidence_ledger=False):
        super().__init__()
        self.flags = {"disable_supersession": disable_supersession,
                      "disable_contradiction_penalty": disable_contradiction_penalty,
                      "disable_authority": disable_authority, "disable_dense": disable_dense,
                      "disable_graph_density": disable_graph_density,
                      "disable_evidence_ledger": disable_evidence_ledger}

    def query(self, instance):
        result = super().query(instance)
        result.trace.update({"pipeline": ["ingest", "distill", "rank", "filters", "compile"], "flags": self.flags,
                             "evidence_ledger": not self.flags["disable_evidence_ledger"]})
        return result


class LegacyCortexAdapter:
    """Bridge for cortex.benchmarks.adapters' pre-v1 public API."""

    name = "cortex"

    def __init__(self, store):
        self.store = store

    def evaluate(self, cases, k=5):
        from cortex.benchmarks.evaluation import evaluate_cortex

        from . import LegacyAdapterResult

        return LegacyAdapterResult(self.name, True, evaluate_cortex(self.store, cases, k=k))
