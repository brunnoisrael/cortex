# Cortex memory benchmark v1

- Corpus: `sha256:d7d76799351f3e8a695b44db8a37ed2b5f52369544360f5ce9b2e5e8fecb5055`
- Revisões: `{"meme": "mvp"}`

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
| absence | cortex | extraction_spurious_rate | 0.0000 | 2/48 | False |
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
| aggregation | bm25 | precision_at_k | 1.0000 | 1/1 | True |
| aggregation | bm25 | provenance_coverage | 1.0000 | 1/1 | True |
| aggregation | bm25 | recall_at_k | 1.0000 | 1/1 | True |
| aggregation | bm25 | scope_accuracy | 1.0000 | 1/1 | True |
| aggregation | bm25 | set_f1 | 1.0000 | 1/1 | True |
| aggregation | bm25 | stale_leak_rate | 0.0000 | 1/48 | False |
| aggregation | bm25 | supersession_accuracy | 1.0000 | 1/1 | True |
| aggregation | bm25 | unsupported_claim_rate | 0.0000 | 1/48 | False |
| aggregation | cortex | abstention_recall | 0.0000 | 1/48 | False |
| aggregation | cortex | answer_support_recall | 0.0000 | 1/48 | False |
| aggregation | cortex | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| aggregation | cortex | current_state_accuracy | 0.0000 | 1/48 | False |
| aggregation | cortex | deletion_compliance | 1.0000 | 1/1 | True |
| aggregation | cortex | evidence_resolution_rate | 1.0000 | 1/1 | True |
| aggregation | cortex | extraction_recall | 0.0000 | 1/48 | False |
| aggregation | cortex | extraction_spurious_rate | 0.0000 | 1/48 | False |
| aggregation | cortex | false_certainty_rate | 0.0000 | 1/48 | False |
| aggregation | cortex | lineage_completeness | 1.0000 | 1/1 | True |
| aggregation | cortex | mrr | 0.0000 | 1/48 | False |
| aggregation | cortex | ndcg_at_k | 0.0000 | 1/48 | False |
| aggregation | cortex | precision_at_k | 0.0000 | 1/48 | False |
| aggregation | cortex | provenance_coverage | 0.0000 | 1/48 | False |
| aggregation | cortex | recall_at_k | 0.0000 | 1/48 | False |
| aggregation | cortex | scope_accuracy | 0.0000 | 1/48 | False |
| aggregation | cortex | set_f1 | 0.0000 | 1/48 | False |
| aggregation | cortex | stale_leak_rate | 0.0000 | 1/48 | False |
| aggregation | cortex | supersession_accuracy | 1.0000 | 1/1 | True |
| aggregation | cortex | unsupported_claim_rate | 0.0000 | 1/48 | False |
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
| cascade | bm25 | mrr | 1.0000 | 1/1 | True |
| cascade | bm25 | ndcg_at_k | 1.0000 | 1/1 | True |
| cascade | bm25 | precision_at_k | 0.5000 | 1/170 | False |
| cascade | bm25 | provenance_coverage | 1.0000 | 1/1 | True |
| cascade | bm25 | recall_at_k | 1.0000 | 1/1 | True |
| cascade | bm25 | scope_accuracy | 0.0000 | 1/48 | False |
| cascade | bm25 | set_f1 | 0.6667 | 1/133 | False |
| cascade | bm25 | stale_leak_rate | 1.0000 | 1/1 | True |
| cascade | bm25 | supersession_accuracy | 0.0000 | 1/48 | False |
| cascade | bm25 | unsupported_claim_rate | 0.0000 | 1/48 | False |
| cascade | cortex | abstention_recall | 0.0000 | 1/48 | False |
| cascade | cortex | answer_support_recall | 0.0000 | 1/48 | False |
| cascade | cortex | cascade_correctness_hop1 | 0.0000 | 1/48 | False |
| cascade | cortex | cascade_correctness_hop2 | 0.0000 | 1/48 | False |
| cascade | cortex | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| cascade | cortex | current_state_accuracy | 0.0000 | 1/48 | False |
| cascade | cortex | deletion_compliance | 1.0000 | 1/1 | True |
| cascade | cortex | evidence_resolution_rate | 1.0000 | 1/1 | True |
| cascade | cortex | extraction_recall | 0.0000 | 1/48 | False |
| cascade | cortex | extraction_spurious_rate | 0.0000 | 1/48 | False |
| cascade | cortex | false_certainty_rate | 0.0000 | 1/48 | False |
| cascade | cortex | lineage_completeness | 0.0000 | 1/48 | False |
| cascade | cortex | mrr | 0.0000 | 1/48 | False |
| cascade | cortex | ndcg_at_k | 0.0000 | 1/48 | False |
| cascade | cortex | precision_at_k | 0.0000 | 1/48 | False |
| cascade | cortex | provenance_coverage | 0.0000 | 1/48 | False |
| cascade | cortex | recall_at_k | 0.0000 | 1/48 | False |
| cascade | cortex | scope_accuracy | 0.0000 | 1/48 | False |
| cascade | cortex | set_f1 | 0.0000 | 1/48 | False |
| cascade | cortex | stale_leak_rate | 0.0000 | 1/48 | False |
| cascade | cortex | supersession_accuracy | 1.0000 | 1/1 | True |
| cascade | cortex | unsupported_claim_rate | 0.0000 | 1/48 | False |
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
| cascade | oracle | precision_at_k | 1.0000 | 1/1 | True |
| cascade | oracle | provenance_coverage | 1.0000 | 1/1 | True |
| cascade | oracle | recall_at_k | 1.0000 | 1/1 | True |
| cascade | oracle | scope_accuracy | 1.0000 | 1/1 | True |
| cascade | oracle | set_f1 | 1.0000 | 1/1 | True |
| cascade | oracle | stale_leak_rate | 0.0000 | 1/48 | False |
| cascade | oracle | supersession_accuracy | 1.0000 | 1/1 | True |
| cascade | oracle | unsupported_claim_rate | 0.0000 | 1/48 | False |
| deletion | bm25 | abstention_recall | 0.0000 | 1/48 | False |
| deletion | bm25 | answer_support_recall | 0.0000 | 1/48 | False |
| deletion | bm25 | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| deletion | bm25 | current_state_accuracy | 1.0000 | 1/1 | True |
| deletion | bm25 | deletion_compliance | 0.0000 | 1/48 | False |
| deletion | bm25 | evidence_resolution_rate | 1.0000 | 1/1 | True |
| deletion | bm25 | false_certainty_rate | 0.0000 | 1/48 | False |
| deletion | bm25 | lineage_completeness | 1.0000 | 1/1 | True |
| deletion | bm25 | mrr | 0.0000 | 1/48 | False |
| deletion | bm25 | ndcg_at_k | 0.0000 | 1/48 | False |
| deletion | bm25 | precision_at_k | 0.0000 | 1/48 | False |
| deletion | bm25 | provenance_coverage | 1.0000 | 1/1 | True |
| deletion | bm25 | recall_at_k | 0.0000 | 1/48 | False |
| deletion | bm25 | scope_accuracy | 0.0000 | 1/48 | False |
| deletion | bm25 | set_f1 | 0.0000 | 1/48 | False |
| deletion | bm25 | stale_leak_rate | 1.0000 | 1/1 | True |
| deletion | bm25 | supersession_accuracy | 0.0000 | 1/48 | False |
| deletion | bm25 | unsupported_claim_rate | 0.0000 | 1/48 | False |
| deletion | cortex | abstention_recall | 1.0000 | 1/1 | True |
| deletion | cortex | answer_support_recall | 0.0000 | 1/48 | False |
| deletion | cortex | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| deletion | cortex | current_state_accuracy | 1.0000 | 1/1 | True |
| deletion | cortex | deletion_compliance | 1.0000 | 1/1 | True |
| deletion | cortex | evidence_resolution_rate | 1.0000 | 1/1 | True |
| deletion | cortex | extraction_recall | 1.0000 | 1/1 | True |
| deletion | cortex | extraction_spurious_rate | 0.0000 | 1/48 | False |
| deletion | cortex | false_certainty_rate | 0.0000 | 1/48 | False |
| deletion | cortex | lineage_completeness | 1.0000 | 1/1 | True |
| deletion | cortex | mrr | 0.0000 | 1/48 | False |
| deletion | cortex | ndcg_at_k | 0.0000 | 1/48 | False |
| deletion | cortex | precision_at_k | 0.0000 | 1/48 | False |
| deletion | cortex | provenance_coverage | 1.0000 | 1/1 | True |
| deletion | cortex | recall_at_k | 0.0000 | 1/48 | False |
| deletion | cortex | scope_accuracy | 1.0000 | 1/1 | True |
| deletion | cortex | set_f1 | 1.0000 | 1/1 | True |
| deletion | cortex | stale_leak_rate | 0.0000 | 1/48 | False |
| deletion | cortex | supersession_accuracy | 1.0000 | 1/1 | True |
| deletion | cortex | unsupported_claim_rate | 0.0000 | 1/48 | False |
| deletion | oracle | abstention_recall | 1.0000 | 1/1 | True |
| deletion | oracle | answer_support_recall | 0.0000 | 1/48 | False |
| deletion | oracle | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| deletion | oracle | current_state_accuracy | 1.0000 | 1/1 | True |
| deletion | oracle | deletion_compliance | 1.0000 | 1/1 | True |
| deletion | oracle | evidence_resolution_rate | 1.0000 | 1/1 | True |
| deletion | oracle | false_certainty_rate | 0.0000 | 1/48 | False |
| deletion | oracle | lineage_completeness | 1.0000 | 1/1 | True |
| deletion | oracle | mrr | 0.0000 | 1/48 | False |
| deletion | oracle | ndcg_at_k | 0.0000 | 1/48 | False |
| deletion | oracle | precision_at_k | 0.0000 | 1/48 | False |
| deletion | oracle | provenance_coverage | 1.0000 | 1/1 | True |
| deletion | oracle | recall_at_k | 0.0000 | 1/48 | False |
| deletion | oracle | scope_accuracy | 1.0000 | 1/1 | True |
| deletion | oracle | set_f1 | 1.0000 | 1/1 | True |
| deletion | oracle | stale_leak_rate | 0.0000 | 1/48 | False |
| deletion | oracle | supersession_accuracy | 1.0000 | 1/1 | True |
| deletion | oracle | unsupported_claim_rate | 0.0000 | 1/48 | False |
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
| exact_recall | bm25 | precision_at_k | 1.0000 | 3/1 | True |
| exact_recall | bm25 | provenance_coverage | 1.0000 | 3/1 | True |
| exact_recall | bm25 | recall_at_k | 1.0000 | 3/1 | True |
| exact_recall | bm25 | scope_accuracy | 1.0000 | 3/1 | True |
| exact_recall | bm25 | set_f1 | 1.0000 | 3/1 | True |
| exact_recall | bm25 | stale_leak_rate | 0.0000 | 3/48 | False |
| exact_recall | bm25 | supersession_accuracy | 1.0000 | 3/1 | True |
| exact_recall | bm25 | unsupported_claim_rate | 0.0000 | 3/48 | False |
| exact_recall | cortex | abstention_recall | 0.0000 | 3/48 | False |
| exact_recall | cortex | answer_support_recall | 0.0000 | 3/48 | False |
| exact_recall | cortex | contradiction_exposure_rate | 0.0000 | 3/48 | False |
| exact_recall | cortex | current_state_accuracy | 0.0000 | 3/48 | False |
| exact_recall | cortex | deletion_compliance | 1.0000 | 3/1 | True |
| exact_recall | cortex | evidence_resolution_rate | 1.0000 | 3/1 | True |
| exact_recall | cortex | extraction_recall | 0.0000 | 3/48 | False |
| exact_recall | cortex | extraction_spurious_rate | 0.0000 | 3/48 | False |
| exact_recall | cortex | false_certainty_rate | 0.0000 | 3/48 | False |
| exact_recall | cortex | lineage_completeness | 1.0000 | 3/1 | True |
| exact_recall | cortex | mrr | 0.0000 | 3/48 | False |
| exact_recall | cortex | ndcg_at_k | 0.0000 | 3/48 | False |
| exact_recall | cortex | precision_at_k | 0.0000 | 3/48 | False |
| exact_recall | cortex | provenance_coverage | 0.0000 | 3/48 | False |
| exact_recall | cortex | recall_at_k | 0.0000 | 3/48 | False |
| exact_recall | cortex | scope_accuracy | 0.0000 | 3/48 | False |
| exact_recall | cortex | set_f1 | 0.0000 | 3/48 | False |
| exact_recall | cortex | stale_leak_rate | 0.0000 | 3/48 | False |
| exact_recall | cortex | supersession_accuracy | 1.0000 | 3/1 | True |
| exact_recall | cortex | unsupported_claim_rate | 0.0000 | 3/48 | False |
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
| tracking | bm25 | abstention_recall | 1.0000 | 2/1 | True |
| tracking | bm25 | answer_support_recall | 1.0000 | 2/1 | True |
| tracking | bm25 | contradiction_exposure_rate | 0.0000 | 2/48 | False |
| tracking | bm25 | current_state_accuracy | 1.0000 | 2/1 | True |
| tracking | bm25 | deletion_compliance | 0.0000 | 2/48 | False |
| tracking | bm25 | evidence_resolution_rate | 1.0000 | 2/1 | True |
| tracking | bm25 | false_certainty_rate | 0.0000 | 2/48 | False |
| tracking | bm25 | lineage_completeness | 1.0000 | 2/1 | True |
| tracking | bm25 | mrr | 0.5000 | 2/170 | False |
| tracking | bm25 | ndcg_at_k | 0.6309 | 2/144 | False |
| tracking | bm25 | precision_at_k | 0.5000 | 2/170 | False |
| tracking | bm25 | provenance_coverage | 1.0000 | 2/1 | True |
| tracking | bm25 | recall_at_k | 1.0000 | 2/1 | True |
| tracking | bm25 | scope_accuracy | 0.0000 | 2/48 | False |
| tracking | bm25 | set_f1 | 0.6667 | 2/133 | False |
| tracking | bm25 | stale_leak_rate | 1.0000 | 2/1 | True |
| tracking | bm25 | supersession_accuracy | 0.0000 | 2/48 | False |
| tracking | bm25 | unsupported_claim_rate | 0.0000 | 2/48 | False |
| tracking | cortex | abstention_recall | 0.5000 | 2/170 | False |
| tracking | cortex | answer_support_recall | 0.5000 | 2/170 | False |
| tracking | cortex | contradiction_exposure_rate | 0.0000 | 2/48 | False |
| tracking | cortex | current_state_accuracy | 0.5000 | 2/170 | False |
| tracking | cortex | deletion_compliance | 1.0000 | 2/1 | True |
| tracking | cortex | evidence_resolution_rate | 1.0000 | 2/1 | True |
| tracking | cortex | extraction_recall | 0.5000 | 2/170 | False |
| tracking | cortex | extraction_spurious_rate | 0.0000 | 2/48 | False |
| tracking | cortex | false_certainty_rate | 0.0000 | 2/48 | False |
| tracking | cortex | lineage_completeness | 0.0000 | 2/48 | False |
| tracking | cortex | mrr | 0.5000 | 2/170 | False |
| tracking | cortex | ndcg_at_k | 0.5000 | 2/170 | False |
| tracking | cortex | precision_at_k | 0.5000 | 2/170 | False |
| tracking | cortex | provenance_coverage | 0.5000 | 2/170 | False |
| tracking | cortex | recall_at_k | 0.5000 | 2/170 | False |
| tracking | cortex | scope_accuracy | 0.5000 | 2/170 | False |
| tracking | cortex | set_f1 | 0.5000 | 2/170 | False |
| tracking | cortex | stale_leak_rate | 0.0000 | 2/48 | False |
| tracking | cortex | supersession_accuracy | 1.0000 | 2/1 | True |
| tracking | cortex | unsupported_claim_rate | 0.0000 | 2/48 | False |
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
| hop | 0 | 10 |
| history_size | s | 3 |
| history_size | xs | 7 |
| filler | nofiller | 10 |

## Comparação pareada (cortex − baseline)

MDE pré-registrado: 0.15. Confirmatório exige n ≥ `required_n`. `holm` marca rejeição após correção dentro da família.

| Métrica | Baseline | n | req n | diff | IC95 | p | holm |
|---|---|---:|---:|---:|---|---:|---|
| cortex_vs_bm25 | abstention_recall | 10 | 121 | -0.3000 | [-0.8000, +0.3000] | 0.2935 | False |
| cortex_vs_bm25 | answer_support_recall | 10 | 121 | -0.6000 | [-0.9000, -0.3000] | 0.0005 | True |
| cortex_vs_bm25 | contradiction_exposure_rate | 10 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_bm25 | current_state_accuracy | 10 | 1 | -0.6000 | [-0.9000, -0.3000] | 0.0005 | True |
| cortex_vs_bm25 | deletion_compliance | 10 | 152 | +0.4000 | [+0.1000, +0.7000] | 0.0205 | False |
| cortex_vs_bm25 | evidence_resolution_rate | 10 | 1 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_bm25 | false_certainty_rate | 10 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_bm25 | lineage_completeness | 10 | 1 | -0.3000 | [-0.6000, +0.0000] | 0.0810 | False |
| cortex_vs_bm25 | mrr | 10 | 152 | -0.5000 | [-0.8000, -0.1500] | 0.0035 | True |
| cortex_vs_bm25 | ndcg_at_k | 10 | 145 | -0.5262 | [-0.8262, -0.1893] | 0.0010 | True |
| cortex_vs_bm25 | precision_at_k | 10 | 163 | -0.4500 | [-0.7500, -0.1500] | 0.0070 | True |
| cortex_vs_bm25 | provenance_coverage | 10 | 1 | -0.6000 | [-0.9000, -0.3000] | 0.0005 | True |
| cortex_vs_bm25 | recall_at_k | 10 | 121 | -0.6000 | [-0.9000, -0.3000] | 0.0005 | True |
| cortex_vs_bm25 | scope_accuracy | 10 | 173 | +0.0000 | [-0.5000, +0.6000] | 1.0000 | False |
| cortex_vs_bm25 | set_f1 | 10 | 152 | -0.2000 | [-0.7000, +0.3667] | 0.4535 | False |
| cortex_vs_bm25 | stale_leak_rate | 10 | 173 | -0.4000 | [-0.7000, -0.1000] | 0.0205 | False |
| cortex_vs_bm25 | supersession_accuracy | 10 | 152 | +0.4000 | [+0.1000, +0.7000] | 0.0205 | False |
| cortex_vs_bm25 | unsupported_claim_rate | 10 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |

### Correção de múltiplas hipóteses (Holm-Bonferroni, por família)

| Família | Comparações | Rejeitadas | menor p | maior p |
|---|---:|---:|---:|---:|
| abstention | 2 | 0 | 0.2935 | 1.0000 |
| evidence | 3 | 1 | 0.0005 | 1.0000 |
| retrieval | 7 | 5 | 0.0005 | 1.0000 |
| temporality | 6 | 1 | 0.0005 | 1.0000 |

## Gates

### G0_reproducibility
- explicit_errors: 0
- leakage_events: 0
- clean: True

### G1_cortex_integrity
- stale_leak_rate_cortex: 0.0
- stale_leak_rate_bm25: 0.4
- stale_leak_rate_raw_context: None
- stale_leak_not_worse_than_bm25: True
- stale_leak_not_worse_than_raw_context: None
- paired_interval_available: True
- exceptions_converted_to_zero: 0

### G2_relative_value
- set_f1: {'comparison': 'cortex_vs_raw_context', 'holm_significant': None, 'n': 0}
- current_state_accuracy: {'comparison': 'cortex_vs_bm25', 'holm_significant': True, 'n': 10, 'diff': -0.6, 'ci_low': -0.9, 'ci_high': -0.3, 'ci_includes_zero': False, 'family': 'temporality', 'required_n': 1, 'minimum_detectable_effect': 0.15, 'power_basis': 'baseline_arm', 'p_value': 0.0005, 'confirmatory': True}
- deletion_compliance: {'comparison': 'cortex_vs_bm25', 'holm_significant': False, 'n': 10, 'diff': 0.4, 'ci_low': 0.1, 'ci_high': 0.7, 'ci_includes_zero': False, 'family': 'temporality', 'required_n': 152, 'minimum_detectable_effect': 0.15, 'power_basis': 'baseline_arm', 'p_value': 0.0205, 'confirmatory': False}
- abstention_recall: {'comparison': 'cortex_vs_bm25', 'holm_significant': False, 'n': 10, 'diff': -0.3, 'ci_low': -0.8, 'ci_high': 0.3, 'ci_includes_zero': True, 'family': 'abstention', 'required_n': 121, 'minimum_detectable_effect': 0.15, 'power_basis': 'baseline_arm', 'p_value': 0.2935, 'confirmatory': False}
- recall_at_k: {'comparison': 'cortex_vs_bm25', 'holm_significant': True, 'n': 10, 'diff': -0.6, 'ci_low': -0.9, 'ci_high': -0.3, 'ci_includes_zero': False, 'family': 'retrieval', 'required_n': 121, 'minimum_detectable_effect': 0.15, 'power_basis': 'baseline_arm', 'p_value': 0.0005, 'confirmatory': False}

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
