from __future__ import annotations

from .base import Adapter, result_for, token_count


class OracleAdapter(Adapter):
    name = "oracle"

    def setup(self, instance):
        super().setup(instance)
        self._gold = instance.gold

    def ingest(self, instance):
        self._events = []

    def query(self, instance):
        evidence = list(self._gold.gold_evidence)
        return result_for(instance, self.name, retrieved=evidence, selected=evidence, evidence=evidence,
                          answer_state="current" if self._gold.current_entities else "unknown",
                          abstained=self._gold.expected_abstention,
                          abstention_reason="gold_expected" if self._gold.expected_abstention else None,
                          missing_evidence=[] if not self._gold.expected_abstention else [instance.query.text],
                          trace={"exploratory": True, "control_only": True},
                          tokens={"input": token_count(instance.query.text), "retrieved": len(evidence), "compiled": len(evidence)})
