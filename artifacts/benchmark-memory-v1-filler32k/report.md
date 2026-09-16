# Cortex memory benchmark v1

- Corpus: `sha256:5fe82cb561434f569454f597b8f78ce2a391808f5f2b92ba2579841fa6136213`
- Revisões: `{"internal": "engineering-memory-v2"}`

## Endpoints por task type

| Task type | Adapter | Endpoint | Mean | n / req n | Confirmatório |
|---|---|---|---:|---|---|
| absence | bm25 | abstention_recall | 0.0000 | 2/48 | False |
| absence | bm25 | answer_support_recall | 0.0000 | 2/48 | False |
| absence | bm25 | contradiction_exposure_rate | 0.0000 | 2/48 | False |
| absence | bm25 | current_state_accuracy | 1.0000 | 2/1 | True |
| absence | bm25 | deletion_compliance | 1.0000 | 2/1 | True |
| absence | bm25 | evidence_resolution_rate | 1.0000 | 2/1 | True |
| absence | bm25 | false_certainty_rate | 0.0000 | 2/48 | False |
| absence | bm25 | lineage_completeness | 1.0000 | 2/1 | True |
| absence | bm25 | mrr | 0.0000 | 2/48 | False |
| absence | bm25 | ndcg_at_k | 0.0000 | 2/48 | False |
| absence | bm25 | precision_at_k | 0.0000 | 2/48 | False |
| absence | bm25 | provenance_coverage | 1.0000 | 2/1 | True |
| absence | bm25 | recall_at_k | 0.0000 | 2/48 | False |
| absence | bm25 | scope_accuracy | 0.0000 | 2/48 | False |
| absence | bm25 | set_f1 | 0.0000 | 2/48 | False |
| absence | bm25 | stale_leak_rate | 0.0000 | 2/48 | False |
| absence | bm25 | supersession_accuracy | 1.0000 | 2/1 | True |
| absence | bm25 | unsupported_claim_rate | 0.0000 | 2/48 | False |
| absence | cortex | abstention_recall | 1.0000 | 2/1 | True |
| absence | cortex | answer_support_recall | 0.0000 | 2/48 | False |
| absence | cortex | contradiction_exposure_rate | 0.0000 | 2/48 | False |
| absence | cortex | current_state_accuracy | 1.0000 | 2/1 | True |
| absence | cortex | deletion_compliance | 1.0000 | 2/1 | True |
| absence | cortex | evidence_resolution_rate | 1.0000 | 2/1 | True |
| absence | cortex | extraction_recall | 1.0000 | 2/1 | True |
| absence | cortex | extraction_spurious_rate | 1.0000 | 2/1 | True |
| absence | cortex | false_certainty_rate | 0.0000 | 2/48 | False |
| absence | cortex | lineage_completeness | 1.0000 | 2/1 | True |
| absence | cortex | mrr | 0.0000 | 2/48 | False |
| absence | cortex | ndcg_at_k | 0.0000 | 2/48 | False |
| absence | cortex | precision_at_k | 0.0000 | 2/48 | False |
| absence | cortex | provenance_coverage | 1.0000 | 2/1 | True |
| absence | cortex | recall_at_k | 0.0000 | 2/48 | False |
| absence | cortex | scope_accuracy | 1.0000 | 2/1 | True |
| absence | cortex | set_f1 | 1.0000 | 2/1 | True |
| absence | cortex | stale_leak_rate | 0.0000 | 2/48 | False |
| absence | cortex | supersession_accuracy | 1.0000 | 2/1 | True |
| absence | cortex | unsupported_claim_rate | 0.0000 | 2/48 | False |
| absence | no_memory | abstention_recall | 1.0000 | 2/1 | True |
| absence | no_memory | answer_support_recall | 0.0000 | 2/48 | False |
| absence | no_memory | contradiction_exposure_rate | 0.0000 | 2/48 | False |
| absence | no_memory | current_state_accuracy | 1.0000 | 2/1 | True |
| absence | no_memory | deletion_compliance | 1.0000 | 2/1 | True |
| absence | no_memory | evidence_resolution_rate | 1.0000 | 2/1 | True |
| absence | no_memory | false_certainty_rate | 0.0000 | 2/48 | False |
| absence | no_memory | lineage_completeness | 1.0000 | 2/1 | True |
| absence | no_memory | mrr | 0.0000 | 2/48 | False |
| absence | no_memory | ndcg_at_k | 0.0000 | 2/48 | False |
| absence | no_memory | precision_at_k | 0.0000 | 2/48 | False |
| absence | no_memory | provenance_coverage | 1.0000 | 2/1 | True |
| absence | no_memory | recall_at_k | 0.0000 | 2/48 | False |
| absence | no_memory | scope_accuracy | 1.0000 | 2/1 | True |
| absence | no_memory | set_f1 | 1.0000 | 2/1 | True |
| absence | no_memory | stale_leak_rate | 0.0000 | 2/48 | False |
| absence | no_memory | supersession_accuracy | 1.0000 | 2/1 | True |
| absence | no_memory | unsupported_claim_rate | 0.0000 | 2/48 | False |
| absence | oracle | abstention_recall | 1.0000 | 2/1 | True |
| absence | oracle | answer_support_recall | 0.0000 | 2/48 | False |
| absence | oracle | contradiction_exposure_rate | 0.0000 | 2/48 | False |
| absence | oracle | current_state_accuracy | 1.0000 | 2/1 | True |
| absence | oracle | deletion_compliance | 1.0000 | 2/1 | True |
| absence | oracle | evidence_resolution_rate | 1.0000 | 2/1 | True |
| absence | oracle | false_certainty_rate | 0.0000 | 2/48 | False |
| absence | oracle | lineage_completeness | 1.0000 | 2/1 | True |
| absence | oracle | mrr | 0.0000 | 2/48 | False |
| absence | oracle | ndcg_at_k | 0.0000 | 2/48 | False |
| absence | oracle | precision_at_k | 0.0000 | 2/48 | False |
| absence | oracle | provenance_coverage | 1.0000 | 2/1 | True |
| absence | oracle | recall_at_k | 0.0000 | 2/48 | False |
| absence | oracle | scope_accuracy | 1.0000 | 2/1 | True |
| absence | oracle | set_f1 | 1.0000 | 2/1 | True |
| absence | oracle | stale_leak_rate | 0.0000 | 2/48 | False |
| absence | oracle | supersession_accuracy | 1.0000 | 2/1 | True |
| absence | oracle | unsupported_claim_rate | 0.0000 | 2/48 | False |
| absence | raw_context | abstention_recall | 0.0000 | 2/48 | False |
| absence | raw_context | answer_support_recall | 0.0000 | 2/48 | False |
| absence | raw_context | contradiction_exposure_rate | 0.0000 | 2/48 | False |
| absence | raw_context | current_state_accuracy | 1.0000 | 2/1 | True |
| absence | raw_context | deletion_compliance | 1.0000 | 2/1 | True |
| absence | raw_context | evidence_resolution_rate | 1.0000 | 2/1 | True |
| absence | raw_context | false_certainty_rate | 0.0000 | 2/48 | False |
| absence | raw_context | lineage_completeness | 1.0000 | 2/1 | True |
| absence | raw_context | mrr | 0.0000 | 2/48 | False |
| absence | raw_context | ndcg_at_k | 0.0000 | 2/48 | False |
| absence | raw_context | precision_at_k | 0.0000 | 2/48 | False |
| absence | raw_context | provenance_coverage | 1.0000 | 2/1 | True |
| absence | raw_context | recall_at_k | 0.0000 | 2/48 | False |
| absence | raw_context | scope_accuracy | 0.0000 | 2/48 | False |
| absence | raw_context | set_f1 | 0.0000 | 2/48 | False |
| absence | raw_context | stale_leak_rate | 0.0000 | 2/48 | False |
| absence | raw_context | supersession_accuracy | 1.0000 | 2/1 | True |
| absence | raw_context | unsupported_claim_rate | 0.0000 | 2/48 | False |
| aggregation | bm25 | abstention_recall | 1.0000 | 1/1 | True |
| aggregation | bm25 | answer_support_recall | 1.0000 | 1/1 | True |
| aggregation | bm25 | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| aggregation | bm25 | current_state_accuracy | 1.0000 | 1/1 | True |
| aggregation | bm25 | deletion_compliance | 1.0000 | 1/1 | True |
| aggregation | bm25 | evidence_resolution_rate | 1.0000 | 1/1 | True |
| aggregation | bm25 | false_certainty_rate | 0.0000 | 1/48 | False |
| aggregation | bm25 | lineage_completeness | 1.0000 | 1/1 | True |
| aggregation | bm25 | mrr | 1.0000 | 1/1 | True |
| aggregation | bm25 | ndcg_at_k | 1.0000 | 1/1 | True |
| aggregation | bm25 | precision_at_k | 0.6000 | 1/152 | False |
| aggregation | bm25 | provenance_coverage | 1.0000 | 1/1 | True |
| aggregation | bm25 | recall_at_k | 1.0000 | 1/1 | True |
| aggregation | bm25 | scope_accuracy | 0.0000 | 1/48 | False |
| aggregation | bm25 | set_f1 | 0.7500 | 1/100 | False |
| aggregation | bm25 | stale_leak_rate | 0.0000 | 1/48 | False |
| aggregation | bm25 | supersession_accuracy | 1.0000 | 1/1 | True |
| aggregation | bm25 | unsupported_claim_rate | 0.0000 | 1/48 | False |
| aggregation | cortex | abstention_recall | 1.0000 | 1/1 | True |
| aggregation | cortex | answer_support_recall | 1.0000 | 1/1 | True |
| aggregation | cortex | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| aggregation | cortex | current_state_accuracy | 1.0000 | 1/1 | True |
| aggregation | cortex | deletion_compliance | 1.0000 | 1/1 | True |
| aggregation | cortex | evidence_resolution_rate | 1.0000 | 1/1 | True |
| aggregation | cortex | extraction_recall | 1.0000 | 1/1 | True |
| aggregation | cortex | extraction_spurious_rate | 0.0000 | 1/48 | False |
| aggregation | cortex | false_certainty_rate | 0.0000 | 1/48 | False |
| aggregation | cortex | lineage_completeness | 1.0000 | 1/1 | True |
| aggregation | cortex | mrr | 1.0000 | 1/1 | True |
| aggregation | cortex | ndcg_at_k | 1.0000 | 1/1 | True |
| aggregation | cortex | precision_at_k | 1.0000 | 1/1 | True |
| aggregation | cortex | provenance_coverage | 1.0000 | 1/1 | True |
| aggregation | cortex | recall_at_k | 1.0000 | 1/1 | True |
| aggregation | cortex | scope_accuracy | 1.0000 | 1/1 | True |
| aggregation | cortex | set_f1 | 1.0000 | 1/1 | True |
| aggregation | cortex | stale_leak_rate | 0.0000 | 1/48 | False |
| aggregation | cortex | supersession_accuracy | 1.0000 | 1/1 | True |
| aggregation | cortex | unsupported_claim_rate | 0.0000 | 1/48 | False |
| aggregation | no_memory | abstention_recall | 0.0000 | 1/48 | False |
| aggregation | no_memory | answer_support_recall | 0.0000 | 1/48 | False |
| aggregation | no_memory | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| aggregation | no_memory | current_state_accuracy | 0.0000 | 1/48 | False |
| aggregation | no_memory | deletion_compliance | 1.0000 | 1/1 | True |
| aggregation | no_memory | evidence_resolution_rate | 1.0000 | 1/1 | True |
| aggregation | no_memory | false_certainty_rate | 0.0000 | 1/48 | False |
| aggregation | no_memory | lineage_completeness | 1.0000 | 1/1 | True |
| aggregation | no_memory | mrr | 0.0000 | 1/48 | False |
| aggregation | no_memory | ndcg_at_k | 0.0000 | 1/48 | False |
| aggregation | no_memory | precision_at_k | 0.0000 | 1/48 | False |
| aggregation | no_memory | provenance_coverage | 0.0000 | 1/48 | False |
| aggregation | no_memory | recall_at_k | 0.0000 | 1/48 | False |
| aggregation | no_memory | scope_accuracy | 0.0000 | 1/48 | False |
| aggregation | no_memory | set_f1 | 0.0000 | 1/48 | False |
| aggregation | no_memory | stale_leak_rate | 0.0000 | 1/48 | False |
| aggregation | no_memory | supersession_accuracy | 1.0000 | 1/1 | True |
| aggregation | no_memory | unsupported_claim_rate | 0.0000 | 1/48 | False |
| aggregation | oracle | abstention_recall | 1.0000 | 1/1 | True |
| aggregation | oracle | answer_support_recall | 1.0000 | 1/1 | True |
| aggregation | oracle | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| aggregation | oracle | current_state_accuracy | 1.0000 | 1/1 | True |
| aggregation | oracle | deletion_compliance | 1.0000 | 1/1 | True |
| aggregation | oracle | evidence_resolution_rate | 1.0000 | 1/1 | True |
| aggregation | oracle | false_certainty_rate | 0.0000 | 1/48 | False |
| aggregation | oracle | lineage_completeness | 1.0000 | 1/1 | True |
| aggregation | oracle | mrr | 1.0000 | 1/1 | True |
| aggregation | oracle | ndcg_at_k | 1.0000 | 1/1 | True |
| aggregation | oracle | precision_at_k | 1.0000 | 1/1 | True |
| aggregation | oracle | provenance_coverage | 1.0000 | 1/1 | True |
| aggregation | oracle | recall_at_k | 1.0000 | 1/1 | True |
| aggregation | oracle | scope_accuracy | 1.0000 | 1/1 | True |
| aggregation | oracle | set_f1 | 1.0000 | 1/1 | True |
| aggregation | oracle | stale_leak_rate | 0.0000 | 1/48 | False |
| aggregation | oracle | supersession_accuracy | 1.0000 | 1/1 | True |
| aggregation | oracle | unsupported_claim_rate | 0.0000 | 1/48 | False |
| aggregation | raw_context | abstention_recall | 1.0000 | 1/1 | True |
| aggregation | raw_context | answer_support_recall | 0.0000 | 1/48 | False |
| aggregation | raw_context | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| aggregation | raw_context | current_state_accuracy | 0.0000 | 1/48 | False |
| aggregation | raw_context | deletion_compliance | 1.0000 | 1/1 | True |
| aggregation | raw_context | evidence_resolution_rate | 1.0000 | 1/1 | True |
| aggregation | raw_context | false_certainty_rate | 0.0000 | 1/48 | False |
| aggregation | raw_context | lineage_completeness | 1.0000 | 1/1 | True |
| aggregation | raw_context | mrr | 0.0000 | 1/48 | False |
| aggregation | raw_context | ndcg_at_k | 0.0000 | 1/48 | False |
| aggregation | raw_context | precision_at_k | 0.0000 | 1/48 | False |
| aggregation | raw_context | provenance_coverage | 0.0000 | 1/48 | False |
| aggregation | raw_context | recall_at_k | 0.0000 | 1/48 | False |
| aggregation | raw_context | scope_accuracy | 0.0000 | 1/48 | False |
| aggregation | raw_context | set_f1 | 0.0000 | 1/48 | False |
| aggregation | raw_context | stale_leak_rate | 0.0000 | 1/48 | False |
| aggregation | raw_context | supersession_accuracy | 1.0000 | 1/1 | True |
| aggregation | raw_context | unsupported_claim_rate | 0.0000 | 1/48 | False |
| cascade | bm25 | abstention_recall | 1.0000 | 1/1 | True |
| cascade | bm25 | answer_support_recall | 1.0000 | 1/1 | True |
| cascade | bm25 | cascade_correctness_hop1 | 0.0000 | 1/48 | False |
| cascade | bm25 | cascade_correctness_hop2 | 0.0000 | 1/48 | False |
| cascade | bm25 | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| cascade | bm25 | current_state_accuracy | 1.0000 | 1/1 | True |
| cascade | bm25 | deletion_compliance | 0.0000 | 1/48 | False |
| cascade | bm25 | evidence_resolution_rate | 1.0000 | 1/1 | True |
| cascade | bm25 | false_certainty_rate | 0.0000 | 1/48 | False |
| cascade | bm25 | lineage_completeness | 1.0000 | 1/1 | True |
| cascade | bm25 | mrr | 0.5000 | 1/170 | False |
| cascade | bm25 | ndcg_at_k | 0.6309 | 1/144 | False |
| cascade | bm25 | precision_at_k | 0.2000 | 1/138 | False |
| cascade | bm25 | provenance_coverage | 1.0000 | 1/1 | True |
| cascade | bm25 | recall_at_k | 1.0000 | 1/1 | True |
| cascade | bm25 | scope_accuracy | 0.0000 | 1/48 | False |
| cascade | bm25 | set_f1 | 0.3333 | 1/168 | False |
| cascade | bm25 | stale_leak_rate | 1.0000 | 1/1 | True |
| cascade | bm25 | supersession_accuracy | 0.0000 | 1/48 | False |
| cascade | bm25 | unsupported_claim_rate | 0.0000 | 1/48 | False |
| cascade | cortex | abstention_recall | 1.0000 | 1/1 | True |
| cascade | cortex | answer_support_recall | 1.0000 | 1/1 | True |
| cascade | cortex | cascade_correctness_hop1 | 1.0000 | 1/1 | True |
| cascade | cortex | cascade_correctness_hop2 | 1.0000 | 1/1 | True |
| cascade | cortex | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| cascade | cortex | current_state_accuracy | 1.0000 | 1/1 | True |
| cascade | cortex | deletion_compliance | 1.0000 | 1/1 | True |
| cascade | cortex | evidence_resolution_rate | 1.0000 | 1/1 | True |
| cascade | cortex | extraction_recall | 1.0000 | 1/1 | True |
| cascade | cortex | extraction_spurious_rate | 0.3333 | 1/168 | False |
| cascade | cortex | false_certainty_rate | 0.0000 | 1/48 | False |
| cascade | cortex | lineage_completeness | 1.0000 | 1/1 | True |
| cascade | cortex | mrr | 0.5000 | 1/170 | False |
| cascade | cortex | ndcg_at_k | 0.6309 | 1/144 | False |
| cascade | cortex | precision_at_k | 0.5000 | 1/170 | False |
| cascade | cortex | provenance_coverage | 1.0000 | 1/1 | True |
| cascade | cortex | recall_at_k | 1.0000 | 1/1 | True |
| cascade | cortex | scope_accuracy | 0.0000 | 1/48 | False |
| cascade | cortex | set_f1 | 0.6667 | 1/133 | False |
| cascade | cortex | stale_leak_rate | 0.0000 | 1/48 | False |
| cascade | cortex | supersession_accuracy | 1.0000 | 1/1 | True |
| cascade | cortex | unsupported_claim_rate | 0.0000 | 1/48 | False |
| cascade | no_memory | abstention_recall | 0.0000 | 1/48 | False |
| cascade | no_memory | answer_support_recall | 0.0000 | 1/48 | False |
| cascade | no_memory | cascade_correctness_hop1 | 0.0000 | 1/48 | False |
| cascade | no_memory | cascade_correctness_hop2 | 0.0000 | 1/48 | False |
| cascade | no_memory | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| cascade | no_memory | current_state_accuracy | 0.0000 | 1/48 | False |
| cascade | no_memory | deletion_compliance | 1.0000 | 1/1 | True |
| cascade | no_memory | evidence_resolution_rate | 1.0000 | 1/1 | True |
| cascade | no_memory | false_certainty_rate | 0.0000 | 1/48 | False |
| cascade | no_memory | lineage_completeness | 0.0000 | 1/48 | False |
| cascade | no_memory | mrr | 0.0000 | 1/48 | False |
| cascade | no_memory | ndcg_at_k | 0.0000 | 1/48 | False |
| cascade | no_memory | precision_at_k | 0.0000 | 1/48 | False |
| cascade | no_memory | provenance_coverage | 0.0000 | 1/48 | False |
| cascade | no_memory | recall_at_k | 0.0000 | 1/48 | False |
| cascade | no_memory | scope_accuracy | 0.0000 | 1/48 | False |
| cascade | no_memory | set_f1 | 0.0000 | 1/48 | False |
| cascade | no_memory | stale_leak_rate | 0.0000 | 1/48 | False |
| cascade | no_memory | supersession_accuracy | 1.0000 | 1/1 | True |
| cascade | no_memory | unsupported_claim_rate | 0.0000 | 1/48 | False |
| cascade | oracle | abstention_recall | 1.0000 | 1/1 | True |
| cascade | oracle | answer_support_recall | 1.0000 | 1/1 | True |
| cascade | oracle | cascade_correctness_hop1 | 0.0000 | 1/48 | False |
| cascade | oracle | cascade_correctness_hop2 | 0.0000 | 1/48 | False |
| cascade | oracle | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| cascade | oracle | current_state_accuracy | 1.0000 | 1/1 | True |
| cascade | oracle | deletion_compliance | 1.0000 | 1/1 | True |
| cascade | oracle | evidence_resolution_rate | 1.0000 | 1/1 | True |
| cascade | oracle | false_certainty_rate | 0.0000 | 1/48 | False |
| cascade | oracle | lineage_completeness | 0.5000 | 1/170 | False |
| cascade | oracle | mrr | 1.0000 | 1/1 | True |
| cascade | oracle | ndcg_at_k | 1.0000 | 1/1 | True |
| cascade | oracle | precision_at_k | 0.5000 | 1/170 | False |
| cascade | oracle | provenance_coverage | 1.0000 | 1/1 | True |
| cascade | oracle | recall_at_k | 1.0000 | 1/1 | True |
| cascade | oracle | scope_accuracy | 0.0000 | 1/48 | False |
| cascade | oracle | set_f1 | 0.6667 | 1/133 | False |
| cascade | oracle | stale_leak_rate | 0.0000 | 1/48 | False |
| cascade | oracle | supersession_accuracy | 1.0000 | 1/1 | True |
| cascade | oracle | unsupported_claim_rate | 0.0000 | 1/48 | False |
| cascade | raw_context | abstention_recall | 1.0000 | 1/1 | True |
| cascade | raw_context | answer_support_recall | 0.0000 | 1/48 | False |
| cascade | raw_context | cascade_correctness_hop1 | 0.0000 | 1/48 | False |
| cascade | raw_context | cascade_correctness_hop2 | 0.0000 | 1/48 | False |
| cascade | raw_context | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| cascade | raw_context | current_state_accuracy | 0.0000 | 1/48 | False |
| cascade | raw_context | deletion_compliance | 1.0000 | 1/1 | True |
| cascade | raw_context | evidence_resolution_rate | 1.0000 | 1/1 | True |
| cascade | raw_context | false_certainty_rate | 0.0000 | 1/48 | False |
| cascade | raw_context | lineage_completeness | 0.0000 | 1/48 | False |
| cascade | raw_context | mrr | 0.0000 | 1/48 | False |
| cascade | raw_context | ndcg_at_k | 0.0000 | 1/48 | False |
| cascade | raw_context | precision_at_k | 0.0000 | 1/48 | False |
| cascade | raw_context | provenance_coverage | 0.0000 | 1/48 | False |
| cascade | raw_context | recall_at_k | 0.0000 | 1/48 | False |
| cascade | raw_context | scope_accuracy | 0.0000 | 1/48 | False |
| cascade | raw_context | set_f1 | 0.0000 | 1/48 | False |
| cascade | raw_context | stale_leak_rate | 0.0000 | 1/48 | False |
| cascade | raw_context | supersession_accuracy | 1.0000 | 1/1 | True |
| cascade | raw_context | unsupported_claim_rate | 0.0000 | 1/48 | False |
| deletion | bm25 | abstention_recall | 1.0000 | 1/1 | True |
| deletion | bm25 | answer_support_recall | 1.0000 | 1/1 | True |
| deletion | bm25 | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| deletion | bm25 | current_state_accuracy | 1.0000 | 1/1 | True |
| deletion | bm25 | deletion_compliance | 0.0000 | 1/48 | False |
| deletion | bm25 | evidence_resolution_rate | 1.0000 | 1/1 | True |
| deletion | bm25 | false_certainty_rate | 0.0000 | 1/48 | False |
| deletion | bm25 | lineage_completeness | 1.0000 | 1/1 | True |
| deletion | bm25 | mrr | 0.5000 | 1/170 | False |
| deletion | bm25 | ndcg_at_k | 0.6309 | 1/144 | False |
| deletion | bm25 | precision_at_k | 0.2000 | 1/138 | False |
| deletion | bm25 | provenance_coverage | 1.0000 | 1/1 | True |
| deletion | bm25 | recall_at_k | 1.0000 | 1/1 | True |
| deletion | bm25 | scope_accuracy | 0.0000 | 1/48 | False |
| deletion | bm25 | set_f1 | 0.3333 | 1/168 | False |
| deletion | bm25 | stale_leak_rate | 1.0000 | 1/1 | True |
| deletion | bm25 | supersession_accuracy | 0.0000 | 1/48 | False |
| deletion | bm25 | unsupported_claim_rate | 0.0000 | 1/48 | False |
| deletion | cortex | abstention_recall | 1.0000 | 1/1 | True |
| deletion | cortex | answer_support_recall | 0.0000 | 1/48 | False |
| deletion | cortex | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| deletion | cortex | current_state_accuracy | 0.0000 | 1/48 | False |
| deletion | cortex | deletion_compliance | 1.0000 | 1/1 | True |
| deletion | cortex | evidence_resolution_rate | 1.0000 | 1/1 | True |
| deletion | cortex | extraction_recall | 1.0000 | 1/1 | True |
| deletion | cortex | extraction_spurious_rate | 0.6667 | 1/133 | False |
| deletion | cortex | false_certainty_rate | 0.0000 | 1/48 | False |
| deletion | cortex | lineage_completeness | 1.0000 | 1/1 | True |
| deletion | cortex | mrr | 0.0000 | 1/48 | False |
| deletion | cortex | ndcg_at_k | 0.0000 | 1/48 | False |
| deletion | cortex | precision_at_k | 0.0000 | 1/48 | False |
| deletion | cortex | provenance_coverage | 0.0000 | 1/48 | False |
| deletion | cortex | recall_at_k | 0.0000 | 1/48 | False |
| deletion | cortex | scope_accuracy | 0.0000 | 1/48 | False |
| deletion | cortex | set_f1 | 0.0000 | 1/48 | False |
| deletion | cortex | stale_leak_rate | 0.0000 | 1/48 | False |
| deletion | cortex | supersession_accuracy | 1.0000 | 1/1 | True |
| deletion | cortex | unsupported_claim_rate | 0.0000 | 1/48 | False |
| deletion | no_memory | abstention_recall | 0.0000 | 1/48 | False |
| deletion | no_memory | answer_support_recall | 0.0000 | 1/48 | False |
| deletion | no_memory | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| deletion | no_memory | current_state_accuracy | 0.0000 | 1/48 | False |
| deletion | no_memory | deletion_compliance | 1.0000 | 1/1 | True |
| deletion | no_memory | evidence_resolution_rate | 1.0000 | 1/1 | True |
| deletion | no_memory | false_certainty_rate | 0.0000 | 1/48 | False |
| deletion | no_memory | lineage_completeness | 0.0000 | 1/48 | False |
| deletion | no_memory | mrr | 0.0000 | 1/48 | False |
| deletion | no_memory | ndcg_at_k | 0.0000 | 1/48 | False |
| deletion | no_memory | precision_at_k | 0.0000 | 1/48 | False |
| deletion | no_memory | provenance_coverage | 0.0000 | 1/48 | False |
| deletion | no_memory | recall_at_k | 0.0000 | 1/48 | False |
| deletion | no_memory | scope_accuracy | 0.0000 | 1/48 | False |
| deletion | no_memory | set_f1 | 0.0000 | 1/48 | False |
| deletion | no_memory | stale_leak_rate | 0.0000 | 1/48 | False |
| deletion | no_memory | supersession_accuracy | 1.0000 | 1/1 | True |
| deletion | no_memory | unsupported_claim_rate | 0.0000 | 1/48 | False |
| deletion | oracle | abstention_recall | 1.0000 | 1/1 | True |
| deletion | oracle | answer_support_recall | 1.0000 | 1/1 | True |
| deletion | oracle | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| deletion | oracle | current_state_accuracy | 1.0000 | 1/1 | True |
| deletion | oracle | deletion_compliance | 1.0000 | 1/1 | True |
| deletion | oracle | evidence_resolution_rate | 1.0000 | 1/1 | True |
| deletion | oracle | false_certainty_rate | 0.0000 | 1/48 | False |
| deletion | oracle | lineage_completeness | 0.5000 | 1/170 | False |
| deletion | oracle | mrr | 1.0000 | 1/1 | True |
| deletion | oracle | ndcg_at_k | 1.0000 | 1/1 | True |
| deletion | oracle | precision_at_k | 1.0000 | 1/1 | True |
| deletion | oracle | provenance_coverage | 1.0000 | 1/1 | True |
| deletion | oracle | recall_at_k | 1.0000 | 1/1 | True |
| deletion | oracle | scope_accuracy | 1.0000 | 1/1 | True |
| deletion | oracle | set_f1 | 1.0000 | 1/1 | True |
| deletion | oracle | stale_leak_rate | 0.0000 | 1/48 | False |
| deletion | oracle | supersession_accuracy | 1.0000 | 1/1 | True |
| deletion | oracle | unsupported_claim_rate | 0.0000 | 1/48 | False |
| deletion | raw_context | abstention_recall | 1.0000 | 1/1 | True |
| deletion | raw_context | answer_support_recall | 0.0000 | 1/48 | False |
| deletion | raw_context | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| deletion | raw_context | current_state_accuracy | 0.0000 | 1/48 | False |
| deletion | raw_context | deletion_compliance | 1.0000 | 1/1 | True |
| deletion | raw_context | evidence_resolution_rate | 1.0000 | 1/1 | True |
| deletion | raw_context | false_certainty_rate | 0.0000 | 1/48 | False |
| deletion | raw_context | lineage_completeness | 0.0000 | 1/48 | False |
| deletion | raw_context | mrr | 0.0000 | 1/48 | False |
| deletion | raw_context | ndcg_at_k | 0.0000 | 1/48 | False |
| deletion | raw_context | precision_at_k | 0.0000 | 1/48 | False |
| deletion | raw_context | provenance_coverage | 0.0000 | 1/48 | False |
| deletion | raw_context | recall_at_k | 0.0000 | 1/48 | False |
| deletion | raw_context | scope_accuracy | 0.0000 | 1/48 | False |
| deletion | raw_context | set_f1 | 0.0000 | 1/48 | False |
| deletion | raw_context | stale_leak_rate | 0.0000 | 1/48 | False |
| deletion | raw_context | supersession_accuracy | 1.0000 | 1/1 | True |
| deletion | raw_context | unsupported_claim_rate | 0.0000 | 1/48 | False |
| exact_recall | bm25 | abstention_recall | 1.0000 | 3/1 | True |
| exact_recall | bm25 | answer_support_recall | 1.0000 | 3/1 | True |
| exact_recall | bm25 | contradiction_exposure_rate | 0.0000 | 3/48 | False |
| exact_recall | bm25 | current_state_accuracy | 1.0000 | 3/1 | True |
| exact_recall | bm25 | deletion_compliance | 1.0000 | 3/1 | True |
| exact_recall | bm25 | evidence_resolution_rate | 1.0000 | 3/1 | True |
| exact_recall | bm25 | false_certainty_rate | 0.0000 | 3/48 | False |
| exact_recall | bm25 | lineage_completeness | 1.0000 | 3/1 | True |
| exact_recall | bm25 | mrr | 1.0000 | 3/1 | True |
| exact_recall | bm25 | ndcg_at_k | 1.0000 | 3/1 | True |
| exact_recall | bm25 | precision_at_k | 0.7333 | 3/107 | False |
| exact_recall | bm25 | provenance_coverage | 1.0000 | 3/1 | True |
| exact_recall | bm25 | recall_at_k | 1.0000 | 3/1 | True |
| exact_recall | bm25 | scope_accuracy | 0.6667 | 3/133 | False |
| exact_recall | bm25 | set_f1 | 0.7778 | 3/87 | False |
| exact_recall | bm25 | stale_leak_rate | 0.0000 | 3/48 | False |
| exact_recall | bm25 | supersession_accuracy | 1.0000 | 3/1 | True |
| exact_recall | bm25 | unsupported_claim_rate | 0.0000 | 3/48 | False |
| exact_recall | cortex | abstention_recall | 1.0000 | 3/1 | True |
| exact_recall | cortex | answer_support_recall | 1.0000 | 3/1 | True |
| exact_recall | cortex | contradiction_exposure_rate | 0.0000 | 3/48 | False |
| exact_recall | cortex | current_state_accuracy | 1.0000 | 3/1 | True |
| exact_recall | cortex | deletion_compliance | 1.0000 | 3/1 | True |
| exact_recall | cortex | evidence_resolution_rate | 1.0000 | 3/1 | True |
| exact_recall | cortex | extraction_recall | 1.0000 | 3/1 | True |
| exact_recall | cortex | extraction_spurious_rate | 0.0000 | 3/48 | False |
| exact_recall | cortex | false_certainty_rate | 0.0000 | 3/48 | False |
| exact_recall | cortex | lineage_completeness | 1.0000 | 3/1 | True |
| exact_recall | cortex | mrr | 1.0000 | 3/1 | True |
| exact_recall | cortex | ndcg_at_k | 1.0000 | 3/1 | True |
| exact_recall | cortex | precision_at_k | 1.0000 | 3/1 | True |
| exact_recall | cortex | provenance_coverage | 1.0000 | 3/1 | True |
| exact_recall | cortex | recall_at_k | 1.0000 | 3/1 | True |
| exact_recall | cortex | scope_accuracy | 1.0000 | 3/1 | True |
| exact_recall | cortex | set_f1 | 1.0000 | 3/1 | True |
| exact_recall | cortex | stale_leak_rate | 0.0000 | 3/48 | False |
| exact_recall | cortex | supersession_accuracy | 1.0000 | 3/1 | True |
| exact_recall | cortex | unsupported_claim_rate | 0.0000 | 3/48 | False |
| exact_recall | no_memory | abstention_recall | 0.0000 | 3/48 | False |
| exact_recall | no_memory | answer_support_recall | 0.0000 | 3/48 | False |
| exact_recall | no_memory | contradiction_exposure_rate | 0.0000 | 3/48 | False |
| exact_recall | no_memory | current_state_accuracy | 0.0000 | 3/48 | False |
| exact_recall | no_memory | deletion_compliance | 1.0000 | 3/1 | True |
| exact_recall | no_memory | evidence_resolution_rate | 1.0000 | 3/1 | True |
| exact_recall | no_memory | false_certainty_rate | 0.0000 | 3/48 | False |
| exact_recall | no_memory | lineage_completeness | 1.0000 | 3/1 | True |
| exact_recall | no_memory | mrr | 0.0000 | 3/48 | False |
| exact_recall | no_memory | ndcg_at_k | 0.0000 | 3/48 | False |
| exact_recall | no_memory | precision_at_k | 0.0000 | 3/48 | False |
| exact_recall | no_memory | provenance_coverage | 0.0000 | 3/48 | False |
| exact_recall | no_memory | recall_at_k | 0.0000 | 3/48 | False |
| exact_recall | no_memory | scope_accuracy | 0.0000 | 3/48 | False |
| exact_recall | no_memory | set_f1 | 0.0000 | 3/48 | False |
| exact_recall | no_memory | stale_leak_rate | 0.0000 | 3/48 | False |
| exact_recall | no_memory | supersession_accuracy | 1.0000 | 3/1 | True |
| exact_recall | no_memory | unsupported_claim_rate | 0.0000 | 3/48 | False |
| exact_recall | oracle | abstention_recall | 1.0000 | 3/1 | True |
| exact_recall | oracle | answer_support_recall | 1.0000 | 3/1 | True |
| exact_recall | oracle | contradiction_exposure_rate | 0.0000 | 3/48 | False |
| exact_recall | oracle | current_state_accuracy | 1.0000 | 3/1 | True |
| exact_recall | oracle | deletion_compliance | 1.0000 | 3/1 | True |
| exact_recall | oracle | evidence_resolution_rate | 1.0000 | 3/1 | True |
| exact_recall | oracle | false_certainty_rate | 0.0000 | 3/48 | False |
| exact_recall | oracle | lineage_completeness | 1.0000 | 3/1 | True |
| exact_recall | oracle | mrr | 1.0000 | 3/1 | True |
| exact_recall | oracle | ndcg_at_k | 1.0000 | 3/1 | True |
| exact_recall | oracle | precision_at_k | 1.0000 | 3/1 | True |
| exact_recall | oracle | provenance_coverage | 1.0000 | 3/1 | True |
| exact_recall | oracle | recall_at_k | 1.0000 | 3/1 | True |
| exact_recall | oracle | scope_accuracy | 1.0000 | 3/1 | True |
| exact_recall | oracle | set_f1 | 1.0000 | 3/1 | True |
| exact_recall | oracle | stale_leak_rate | 0.0000 | 3/48 | False |
| exact_recall | oracle | supersession_accuracy | 1.0000 | 3/1 | True |
| exact_recall | oracle | unsupported_claim_rate | 0.0000 | 3/48 | False |
| exact_recall | raw_context | abstention_recall | 1.0000 | 3/1 | True |
| exact_recall | raw_context | answer_support_recall | 0.0000 | 3/48 | False |
| exact_recall | raw_context | contradiction_exposure_rate | 0.0000 | 3/48 | False |
| exact_recall | raw_context | current_state_accuracy | 0.0000 | 3/48 | False |
| exact_recall | raw_context | deletion_compliance | 1.0000 | 3/1 | True |
| exact_recall | raw_context | evidence_resolution_rate | 1.0000 | 3/1 | True |
| exact_recall | raw_context | false_certainty_rate | 0.0000 | 3/48 | False |
| exact_recall | raw_context | lineage_completeness | 1.0000 | 3/1 | True |
| exact_recall | raw_context | mrr | 0.0000 | 3/48 | False |
| exact_recall | raw_context | ndcg_at_k | 0.0000 | 3/48 | False |
| exact_recall | raw_context | precision_at_k | 0.0000 | 3/48 | False |
| exact_recall | raw_context | provenance_coverage | 0.0000 | 3/48 | False |
| exact_recall | raw_context | recall_at_k | 0.0000 | 3/48 | False |
| exact_recall | raw_context | scope_accuracy | 0.0000 | 3/48 | False |
| exact_recall | raw_context | set_f1 | 0.0000 | 3/48 | False |
| exact_recall | raw_context | stale_leak_rate | 0.0000 | 3/48 | False |
| exact_recall | raw_context | supersession_accuracy | 1.0000 | 3/1 | True |
| exact_recall | raw_context | unsupported_claim_rate | 0.0000 | 3/48 | False |
| tracking | bm25 | abstention_recall | 1.0000 | 2/1 | True |
| tracking | bm25 | answer_support_recall | 1.0000 | 2/1 | True |
| tracking | bm25 | contradiction_exposure_rate | 0.0000 | 2/48 | False |
| tracking | bm25 | current_state_accuracy | 1.0000 | 2/1 | True |
| tracking | bm25 | deletion_compliance | 0.0000 | 2/48 | False |
| tracking | bm25 | evidence_resolution_rate | 1.0000 | 2/1 | True |
| tracking | bm25 | false_certainty_rate | 0.0000 | 2/48 | False |
| tracking | bm25 | lineage_completeness | 1.0000 | 2/1 | True |
| tracking | bm25 | mrr | 1.0000 | 2/1 | True |
| tracking | bm25 | ndcg_at_k | 1.0000 | 2/1 | True |
| tracking | bm25 | precision_at_k | 0.2000 | 2/138 | False |
| tracking | bm25 | provenance_coverage | 1.0000 | 2/1 | True |
| tracking | bm25 | recall_at_k | 1.0000 | 2/1 | True |
| tracking | bm25 | scope_accuracy | 0.0000 | 2/48 | False |
| tracking | bm25 | set_f1 | 0.3333 | 2/168 | False |
| tracking | bm25 | stale_leak_rate | 1.0000 | 2/1 | True |
| tracking | bm25 | supersession_accuracy | 0.0000 | 2/48 | False |
| tracking | bm25 | unsupported_claim_rate | 0.0000 | 2/48 | False |
| tracking | cortex | abstention_recall | 1.0000 | 2/1 | True |
| tracking | cortex | answer_support_recall | 1.0000 | 2/1 | True |
| tracking | cortex | contradiction_exposure_rate | 0.0000 | 2/48 | False |
| tracking | cortex | current_state_accuracy | 1.0000 | 2/1 | True |
| tracking | cortex | deletion_compliance | 1.0000 | 2/1 | True |
| tracking | cortex | evidence_resolution_rate | 1.0000 | 2/1 | True |
| tracking | cortex | extraction_recall | 1.0000 | 2/1 | True |
| tracking | cortex | extraction_spurious_rate | 0.5000 | 2/170 | False |
| tracking | cortex | false_certainty_rate | 0.0000 | 2/48 | False |
| tracking | cortex | lineage_completeness | 1.0000 | 2/1 | True |
| tracking | cortex | mrr | 1.0000 | 2/1 | True |
| tracking | cortex | ndcg_at_k | 1.0000 | 2/1 | True |
| tracking | cortex | precision_at_k | 1.0000 | 2/1 | True |
| tracking | cortex | provenance_coverage | 1.0000 | 2/1 | True |
| tracking | cortex | recall_at_k | 1.0000 | 2/1 | True |
| tracking | cortex | scope_accuracy | 1.0000 | 2/1 | True |
| tracking | cortex | set_f1 | 1.0000 | 2/1 | True |
| tracking | cortex | stale_leak_rate | 0.0000 | 2/48 | False |
| tracking | cortex | supersession_accuracy | 1.0000 | 2/1 | True |
| tracking | cortex | unsupported_claim_rate | 0.0000 | 2/48 | False |
| tracking | no_memory | abstention_recall | 0.0000 | 2/48 | False |
| tracking | no_memory | answer_support_recall | 0.0000 | 2/48 | False |
| tracking | no_memory | contradiction_exposure_rate | 0.0000 | 2/48 | False |
| tracking | no_memory | current_state_accuracy | 0.0000 | 2/48 | False |
| tracking | no_memory | deletion_compliance | 1.0000 | 2/1 | True |
| tracking | no_memory | evidence_resolution_rate | 1.0000 | 2/1 | True |
| tracking | no_memory | false_certainty_rate | 0.0000 | 2/48 | False |
| tracking | no_memory | lineage_completeness | 0.0000 | 2/48 | False |
| tracking | no_memory | mrr | 0.0000 | 2/48 | False |
| tracking | no_memory | ndcg_at_k | 0.0000 | 2/48 | False |
| tracking | no_memory | precision_at_k | 0.0000 | 2/48 | False |
| tracking | no_memory | provenance_coverage | 0.0000 | 2/48 | False |
| tracking | no_memory | recall_at_k | 0.0000 | 2/48 | False |
| tracking | no_memory | scope_accuracy | 0.0000 | 2/48 | False |
| tracking | no_memory | set_f1 | 0.0000 | 2/48 | False |
| tracking | no_memory | stale_leak_rate | 0.0000 | 2/48 | False |
| tracking | no_memory | supersession_accuracy | 1.0000 | 2/1 | True |
| tracking | no_memory | unsupported_claim_rate | 0.0000 | 2/48 | False |
| tracking | oracle | abstention_recall | 1.0000 | 2/1 | True |
| tracking | oracle | answer_support_recall | 1.0000 | 2/1 | True |
| tracking | oracle | contradiction_exposure_rate | 0.0000 | 2/48 | False |
| tracking | oracle | current_state_accuracy | 1.0000 | 2/1 | True |
| tracking | oracle | deletion_compliance | 1.0000 | 2/1 | True |
| tracking | oracle | evidence_resolution_rate | 1.0000 | 2/1 | True |
| tracking | oracle | false_certainty_rate | 0.0000 | 2/48 | False |
| tracking | oracle | lineage_completeness | 0.5000 | 2/170 | False |
| tracking | oracle | mrr | 1.0000 | 2/1 | True |
| tracking | oracle | ndcg_at_k | 1.0000 | 2/1 | True |
| tracking | oracle | precision_at_k | 1.0000 | 2/1 | True |
| tracking | oracle | provenance_coverage | 1.0000 | 2/1 | True |
| tracking | oracle | recall_at_k | 1.0000 | 2/1 | True |
| tracking | oracle | scope_accuracy | 1.0000 | 2/1 | True |
| tracking | oracle | set_f1 | 1.0000 | 2/1 | True |
| tracking | oracle | stale_leak_rate | 0.0000 | 2/48 | False |
| tracking | oracle | supersession_accuracy | 1.0000 | 2/1 | True |
| tracking | oracle | unsupported_claim_rate | 0.0000 | 2/48 | False |
| tracking | raw_context | abstention_recall | 1.0000 | 2/1 | True |
| tracking | raw_context | answer_support_recall | 0.0000 | 2/48 | False |
| tracking | raw_context | contradiction_exposure_rate | 0.0000 | 2/48 | False |
| tracking | raw_context | current_state_accuracy | 0.0000 | 2/48 | False |
| tracking | raw_context | deletion_compliance | 1.0000 | 2/1 | True |
| tracking | raw_context | evidence_resolution_rate | 1.0000 | 2/1 | True |
| tracking | raw_context | false_certainty_rate | 0.0000 | 2/48 | False |
| tracking | raw_context | lineage_completeness | 0.0000 | 2/48 | False |
| tracking | raw_context | mrr | 0.0000 | 2/48 | False |
| tracking | raw_context | ndcg_at_k | 0.0000 | 2/48 | False |
| tracking | raw_context | precision_at_k | 0.0000 | 2/48 | False |
| tracking | raw_context | provenance_coverage | 0.0000 | 2/48 | False |
| tracking | raw_context | recall_at_k | 0.0000 | 2/48 | False |
| tracking | raw_context | scope_accuracy | 0.0000 | 2/48 | False |
| tracking | raw_context | set_f1 | 0.0000 | 2/48 | False |
| tracking | raw_context | stale_leak_rate | 0.0000 | 2/48 | False |
| tracking | raw_context | supersession_accuracy | 1.0000 | 2/1 | True |
| tracking | raw_context | unsupported_claim_rate | 0.0000 | 2/48 | False |

## Estratificação da amostra (plano §9.1)

Contagem de casos únicos por eixo — uma média única nunca revela se a amostra está concentrada em um hop, tamanho de histórico ou carga de filler.

| Eixo | Bucket | n (casos) |
|---|---|---:|
| task_type | absence | 2 |
| task_type | aggregation | 1 |
| task_type | cascade | 1 |
| task_type | deletion | 1 |
| task_type | exact_recall | 3 |
| task_type | tracking | 2 |
| hop | 0 | 6 |
| hop | 1 | 3 |
| hop | 2 | 1 |
| history_size | l | 10 |
| filler | filler32k | 10 |

## Comparação pareada (cortex − baseline)

MDE pré-registrado: 0.15. Confirmatório exige n ≥ `required_n`. `holm` marca rejeição após correção dentro da família.

| Métrica | Baseline | n | req n | diff | IC95 | p | holm |
|---|---|---:|---:|---:|---|---:|---|
| cortex_vs_bm25 | abstention_recall | 10 | 76 | +0.2000 | [+0.0000, +0.5000] | 0.2375 | False |
| cortex_vs_raw_context | abstention_recall | 10 | 76 | +0.2000 | [+0.0000, +0.5000] | 0.2375 | False |
| cortex_vs_no_memory | abstention_recall | 10 | 138 | +0.8000 | [+0.5000, +1.0000] | 0.0005 | True |
| cortex_vs_bm25 | answer_support_recall | 10 | 76 | -0.1000 | [-0.3000, +0.0000] | 0.6125 | False |
| cortex_vs_raw_context | answer_support_recall | 10 | 48 | +0.7000 | [+0.4000, +0.9000] | 0.0005 | True |
| cortex_vs_no_memory | answer_support_recall | 10 | 48 | +0.7000 | [+0.4000, +0.9000] | 0.0005 | True |
| cortex_vs_bm25 | contradiction_exposure_rate | 10 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_raw_context | contradiction_exposure_rate | 10 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_no_memory | contradiction_exposure_rate | 10 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_bm25 | current_state_accuracy | 10 | 1 | -0.1000 | [-0.3000, +0.0000] | 0.6125 | False |
| cortex_vs_raw_context | current_state_accuracy | 10 | 138 | +0.7000 | [+0.4000, +0.9000] | 0.0005 | True |
| cortex_vs_no_memory | current_state_accuracy | 10 | 138 | +0.7000 | [+0.4000, +0.9000] | 0.0005 | True |
| cortex_vs_bm25 | deletion_compliance | 10 | 152 | +0.4000 | [+0.1000, +0.7000] | 0.0170 | False |
| cortex_vs_raw_context | deletion_compliance | 10 | 1 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_no_memory | deletion_compliance | 10 | 1 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_bm25 | evidence_resolution_rate | 10 | 1 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_raw_context | evidence_resolution_rate | 10 | 1 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_no_memory | evidence_resolution_rate | 10 | 1 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_bm25 | false_certainty_rate | 10 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_raw_context | false_certainty_rate | 10 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_no_memory | false_certainty_rate | 10 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_bm25 | lineage_completeness | 10 | 1 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_raw_context | lineage_completeness | 10 | 152 | +0.4000 | [+0.1000, +0.7000] | 0.0170 | False |
| cortex_vs_no_memory | lineage_completeness | 10 | 152 | +0.4000 | [+0.1000, +0.7000] | 0.0170 | False |
| cortex_vs_bm25 | mrr | 10 | 121 | -0.0500 | [-0.1500, +0.0000] | 0.6125 | False |
| cortex_vs_raw_context | mrr | 10 | 48 | +0.6500 | [+0.3500, +0.9000] | 0.0005 | True |
| cortex_vs_no_memory | mrr | 10 | 48 | +0.6500 | [+0.3500, +0.9000] | 0.0005 | True |
| cortex_vs_bm25 | ndcg_at_k | 10 | 110 | -0.0631 | [-0.1893, +0.0000] | 0.6125 | False |
| cortex_vs_raw_context | ndcg_at_k | 10 | 48 | +0.6631 | [+0.3893, +0.9000] | 0.0005 | True |
| cortex_vs_no_memory | ndcg_at_k | 10 | 48 | +0.6631 | [+0.3893, +0.9000] | 0.0005 | True |
| cortex_vs_bm25 | precision_at_k | 10 | 171 | +0.2900 | [+0.0700, +0.5400] | 0.0135 | False |
| cortex_vs_raw_context | precision_at_k | 10 | 48 | +0.6500 | [+0.3500, +0.9000] | 0.0005 | True |
| cortex_vs_no_memory | precision_at_k | 10 | 48 | +0.6500 | [+0.3500, +0.9000] | 0.0005 | True |
| cortex_vs_bm25 | provenance_coverage | 10 | 1 | -0.1000 | [-0.3000, +0.0000] | 0.6125 | False |
| cortex_vs_raw_context | provenance_coverage | 10 | 138 | +0.7000 | [+0.4000, +0.9000] | 0.0005 | True |
| cortex_vs_no_memory | provenance_coverage | 10 | 138 | +0.7000 | [+0.4000, +0.9000] | 0.0005 | True |
| cortex_vs_bm25 | recall_at_k | 10 | 76 | -0.1000 | [-0.3000, +0.0000] | 0.6125 | False |
| cortex_vs_raw_context | recall_at_k | 10 | 48 | +0.7000 | [+0.4000, +0.9000] | 0.0005 | True |
| cortex_vs_no_memory | recall_at_k | 10 | 48 | +0.7000 | [+0.4000, +0.9000] | 0.0005 | True |
| cortex_vs_bm25 | scope_accuracy | 10 | 138 | +0.6000 | [+0.3000, +0.9000] | 0.0005 | True |
| cortex_vs_raw_context | scope_accuracy | 10 | 48 | +0.8000 | [+0.5000, +1.0000] | 0.0005 | True |
| cortex_vs_no_memory | scope_accuracy | 10 | 138 | +0.6000 | [+0.3000, +0.9000] | 0.0005 | True |
| cortex_vs_bm25 | set_f1 | 10 | 174 | +0.4250 | [+0.1583, +0.6667] | 0.0005 | True |
| cortex_vs_raw_context | set_f1 | 10 | 48 | +0.8667 | [+0.6333, +1.0000] | 0.0005 | True |
| cortex_vs_no_memory | set_f1 | 10 | 138 | +0.6667 | [+0.4000, +0.9000] | 0.0005 | True |
| cortex_vs_bm25 | stale_leak_rate | 10 | 173 | -0.4000 | [-0.7000, -0.1000] | 0.0170 | False |
| cortex_vs_raw_context | stale_leak_rate | 10 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_no_memory | stale_leak_rate | 10 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_bm25 | supersession_accuracy | 10 | 152 | +0.4000 | [+0.1000, +0.7000] | 0.0170 | False |
| cortex_vs_raw_context | supersession_accuracy | 10 | 1 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_no_memory | supersession_accuracy | 10 | 1 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_bm25 | unsupported_claim_rate | 10 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_raw_context | unsupported_claim_rate | 10 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_no_memory | unsupported_claim_rate | 10 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |

### Correção de múltiplas hipóteses (Holm-Bonferroni, por família)

| Família | Comparações | Rejeitadas | menor p | maior p |
|---|---:|---:|---:|---:|
| abstention | 6 | 1 | 0.0005 | 1.0000 |
| evidence | 9 | 2 | 0.0005 | 1.0000 |
| retrieval | 21 | 16 | 0.0005 | 0.6125 |
| temporality | 18 | 2 | 0.0005 | 1.0000 |

## Gates

### G0_reproducibility
- explicit_errors: 0
- leakage_events: 0
- clean: True

### G1_cortex_integrity
- stale_leak_rate_cortex: 0.0
- stale_leak_rate_bm25: 0.4
- stale_leak_rate_raw_context: 0.0
- stale_leak_not_worse_than_bm25: True
- stale_leak_not_worse_than_raw_context: True
- paired_interval_available: True
- exceptions_converted_to_zero: 0

### G2_relative_value
- set_f1: {'comparison': 'cortex_vs_raw_context', 'holm_significant': True, 'n': 10, 'diff': 0.866666667, 'ci_low': 0.633333334, 'ci_high': 1.0, 'ci_includes_zero': False, 'family': 'retrieval', 'required_n': 48, 'minimum_detectable_effect': 0.15, 'power_basis': 'baseline_arm', 'p_value': 0.0005, 'confirmatory': False}
- current_state_accuracy: {'comparison': 'cortex_vs_bm25', 'holm_significant': False, 'n': 10, 'diff': -0.1, 'ci_low': -0.3, 'ci_high': 0.0, 'ci_includes_zero': True, 'family': 'temporality', 'required_n': 1, 'minimum_detectable_effect': 0.15, 'power_basis': 'baseline_arm', 'p_value': 0.6125, 'confirmatory': True}
- deletion_compliance: {'comparison': 'cortex_vs_bm25', 'holm_significant': False, 'n': 10, 'diff': 0.4, 'ci_low': 0.1, 'ci_high': 0.7, 'ci_includes_zero': False, 'family': 'temporality', 'required_n': 152, 'minimum_detectable_effect': 0.15, 'power_basis': 'baseline_arm', 'p_value': 0.017, 'confirmatory': False}
- abstention_recall: {'comparison': 'cortex_vs_bm25', 'holm_significant': False, 'n': 10, 'diff': 0.2, 'ci_low': 0.0, 'ci_high': 0.5, 'ci_includes_zero': True, 'family': 'abstention', 'required_n': 76, 'minimum_detectable_effect': 0.15, 'power_basis': 'baseline_arm', 'p_value': 0.2375, 'confirmatory': False}
- recall_at_k: {'comparison': 'cortex_vs_bm25', 'holm_significant': False, 'n': 10, 'diff': -0.1, 'ci_low': -0.3, 'ci_high': 0.0, 'ci_includes_zero': True, 'family': 'retrieval', 'required_n': 76, 'minimum_detectable_effect': 0.15, 'power_basis': 'baseline_arm', 'p_value': 0.6125, 'confirmatory': False}

### G3_assertion_safety
- false_certainty_reported_per_case: True
- unsupported_claim_rate: 0.0
- evidence_resolution_rate: 1.0

## Eficiência

Latência por fase, percentis e custo por token são publicados em `pareto.json`: não fazem parte do payload determinístico (plano §7).


## Segurança

- Erros explícitos: 0
- Eventos de leakage: 0

## Decisão de produto

`reduzir_claim`

Decisões possíveis (plano §17): promover, recalibrar, reduzir_claim, bloquear_expansao.
Uma média única nunca é o resultado final; ver `summary.json` por task type e split.
