# Cortex memory benchmark v1

## Endpoints

| Adapter | Endpoint | Mean | n | Confirmatory |
|---|---|---:|---:|---|
| bm25 | abstention_recall | 0.7000 | 10 | True |
| bm25 | cascade_correctness_hop1 | 0.0000 | 1 | False |
| bm25 | cascade_correctness_hop2 | 0.0000 | 1 | False |
| bm25 | contradiction_exposure_rate | 0.0000 | 10 | True |
| bm25 | deletion_compliance | 0.6000 | 10 | True |
| bm25 | evidence_resolution_rate | 1.0000 | 10 | True |
| bm25 | false_certainty_rate | 0.0000 | 10 | True |
| bm25 | lineage_completeness | 1.0000 | 10 | True |
| bm25 | mrr | 0.6000 | 10 | True |
| bm25 | ndcg_at_k | 0.6262 | 10 | True |
| bm25 | precision_at_k | 0.5500 | 10 | True |
| bm25 | recall_at_k | 0.7000 | 10 | True |
| bm25 | stale_leak_rate | 0.4000 | 10 | True |
| bm25 | unsupported_claim_rate | 0.0000 | 10 | True |
| bm25_temporal | abstention_recall | 0.7000 | 10 | True |
| bm25_temporal | cascade_correctness_hop1 | 0.0000 | 1 | False |
| bm25_temporal | cascade_correctness_hop2 | 0.0000 | 1 | False |
| bm25_temporal | contradiction_exposure_rate | 0.0000 | 10 | True |
| bm25_temporal | deletion_compliance | 1.0000 | 10 | True |
| bm25_temporal | evidence_resolution_rate | 1.0000 | 10 | True |
| bm25_temporal | false_certainty_rate | 0.7000 | 10 | True |
| bm25_temporal | lineage_completeness | 0.7000 | 10 | True |
| bm25_temporal | mrr | 0.0000 | 10 | True |
| bm25_temporal | ndcg_at_k | 0.0000 | 10 | True |
| bm25_temporal | precision_at_k | 0.0000 | 10 | True |
| bm25_temporal | recall_at_k | 0.0000 | 10 | True |
| bm25_temporal | stale_leak_rate | 0.0000 | 10 | True |
| bm25_temporal | unsupported_claim_rate | 0.0000 | 10 | True |
| cortex | abstention_recall | 0.7000 | 10 | True |
| cortex | cascade_correctness_hop1 | 0.0000 | 1 | False |
| cortex | cascade_correctness_hop2 | 0.0000 | 1 | False |
| cortex | contradiction_exposure_rate | 0.0000 | 10 | True |
| cortex | deletion_compliance | 0.6000 | 10 | True |
| cortex | evidence_resolution_rate | 1.0000 | 10 | True |
| cortex | false_certainty_rate | 0.0000 | 10 | True |
| cortex | lineage_completeness | 1.0000 | 10 | True |
| cortex | mrr | 0.6000 | 10 | True |
| cortex | ndcg_at_k | 0.6262 | 10 | True |
| cortex | precision_at_k | 0.5500 | 10 | True |
| cortex | recall_at_k | 0.7000 | 10 | True |
| cortex | stale_leak_rate | 0.4000 | 10 | True |
| cortex | unsupported_claim_rate | 0.0000 | 10 | True |
| no_memory | abstention_recall | 0.3000 | 10 | True |
| no_memory | cascade_correctness_hop1 | 0.0000 | 1 | False |
| no_memory | cascade_correctness_hop2 | 0.0000 | 1 | False |
| no_memory | contradiction_exposure_rate | 0.0000 | 10 | True |
| no_memory | deletion_compliance | 1.0000 | 10 | True |
| no_memory | evidence_resolution_rate | 1.0000 | 10 | True |
| no_memory | false_certainty_rate | 0.0000 | 10 | True |
| no_memory | lineage_completeness | 0.7000 | 10 | True |
| no_memory | mrr | 0.0000 | 10 | True |
| no_memory | ndcg_at_k | 0.0000 | 10 | True |
| no_memory | precision_at_k | 0.0000 | 10 | True |
| no_memory | recall_at_k | 0.0000 | 10 | True |
| no_memory | stale_leak_rate | 0.0000 | 10 | True |
| no_memory | unsupported_claim_rate | 0.0000 | 10 | True |
| oracle | abstention_recall | 1.0000 | 10 | True |
| oracle | cascade_correctness_hop1 | 0.0000 | 1 | False |
| oracle | cascade_correctness_hop2 | 0.0000 | 1 | False |
| oracle | contradiction_exposure_rate | 0.0000 | 10 | True |
| oracle | deletion_compliance | 1.0000 | 10 | True |
| oracle | evidence_resolution_rate | 1.0000 | 10 | True |
| oracle | false_certainty_rate | 0.0000 | 10 | True |
| oracle | lineage_completeness | 0.8500 | 10 | True |
| oracle | mrr | 0.7000 | 10 | True |
| oracle | ndcg_at_k | 0.7000 | 10 | True |
| oracle | precision_at_k | 0.7000 | 10 | True |
| oracle | recall_at_k | 0.7000 | 10 | True |
| oracle | stale_leak_rate | 0.0000 | 10 | True |
| oracle | unsupported_claim_rate | 0.0000 | 10 | True |
| raw_context | abstention_recall | 0.7000 | 10 | True |
| raw_context | cascade_correctness_hop1 | 0.0000 | 1 | False |
| raw_context | cascade_correctness_hop2 | 0.0000 | 1 | False |
| raw_context | contradiction_exposure_rate | 0.0000 | 10 | True |
| raw_context | deletion_compliance | 0.6000 | 10 | True |
| raw_context | evidence_resolution_rate | 1.0000 | 10 | True |
| raw_context | false_certainty_rate | 0.0000 | 10 | True |
| raw_context | lineage_completeness | 1.0000 | 10 | True |
| raw_context | mrr | 0.5500 | 10 | True |
| raw_context | ndcg_at_k | 0.5893 | 10 | True |
| raw_context | precision_at_k | 0.5500 | 10 | True |
| raw_context | recall_at_k | 0.7000 | 10 | True |
| raw_context | stale_leak_rate | 0.4000 | 10 | True |
| raw_context | unsupported_claim_rate | 0.0000 | 10 | True |

## Safety

- Explicit errors: 0
- Leakage events: 0
- Product decision: diagnostic only until external datasets and confirmatory power are frozen.
- Stale-leak gate and paired intervals are reported in `summary.json`; this MVP does not make a product claim.
