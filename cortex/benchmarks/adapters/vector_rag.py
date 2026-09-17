"""Standard Dense Vector RAG baseline adapter for benchmark v1.

Simulates the industry-standard conversational RAG pipeline:
- No epistemic authority modeling
- No temporal supersession / invalidation policy
- No Evidence Ledger or AST verification
- Dense semantic similarity retrieval over raw session chunks
"""

from __future__ import annotations

import hashlib
import math
import re

from .base import Adapter, case_events, result_for, token_count


class VectorRAGAdapter(Adapter):
    name = "vector_rag"

    # A fixed, offline encoder makes this baseline reproducible on machines
    # without optional model weights.  It is intentionally not Cortex's
    # governed retrieval pipeline.
    encoder = "hash-ngrams/v1"

    @staticmethod
    def _encode(text: str, dimensions: int = 256) -> list[float]:
        clean = re.sub(r"\s+", " ", text.lower().strip())
        features = [*clean.split()]
        features.extend(clean[i:i + 3] for i in range(max(0, len(clean) - 2)))
        vector = [0.0] * dimensions
        for feature in features:
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest, "big") % dimensions
            sign = 1.0 if digest[0] & 1 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector

    @classmethod
    def _similarity(cls, left: str, right: str) -> float:
        a, b = cls._encode(left), cls._encode(right)
        return round(max(0.0, sum(x * y for x, y in zip(a, b, strict=True))), 4)

    def setup(self, instance):
        super().setup(instance)

    def ingest(self, instance):
        self._events = case_events(instance)

    def query(self, instance):
        query_text = instance.query.text
        scored = []
        for eid, content, _session_ts, _event_ts in self._events:
            sim = self._similarity(query_text, content)
            if sim > 0.0:
                scored.append((sim, eid, content))

        # Sort strictly by dense semantic similarity descending
        scored.sort(key=lambda row: (-row[0], row[1]))
        top = [row[1] for row in scored[:5]]

        return result_for(
            instance,
            self.name,
            retrieved=top,
            selected=top,
            evidence=top,
            trace={
                "scores": {eid: round(score, 6) for score, eid, _ in scored[:5]},
                "pipeline": ["fixed_local_encoder", "cosine_similarity", "top_k"],
                "encoder": self.encoder,
                "authority_filter": False,
                "supersession_filter": False,
                "evidence_ledger": False,
            },
            tokens={
                "input": token_count(instance.query.text),
                "retrieved": sum(token_count(row[2]) for row in scored[:5]),
                "compiled": 0,
            },
        )
