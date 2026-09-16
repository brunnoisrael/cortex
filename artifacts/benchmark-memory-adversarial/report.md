# Cortex memory benchmark v1

- Corpus: `sha256:53b4b35d5eedd299274149269199fa04bf87725e122ca1a689536d3e2a40002f`
- Revisões: `{"internal": "engineering-memory-v2"}`

## Endpoints por task type

| Task type | Adapter | Endpoint | Mean | n / req n | Confirmatório |
|---|---|---|---:|---|---|
| absence | bm25 | abstention_recall | 1.0000 | 1/1 | True |
| absence | bm25 | answer_support_recall | 1.0000 | 1/1 | True |
| absence | bm25 | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| absence | bm25 | current_state_accuracy | 1.0000 | 1/1 | True |
| absence | bm25 | deletion_compliance | 0.0000 | 1/48 | False |
| absence | bm25 | evidence_resolution_rate | 1.0000 | 1/1 | True |
| absence | bm25 | false_certainty_rate | 0.0000 | 1/48 | False |
| absence | bm25 | lineage_completeness | 1.0000 | 1/1 | True |
| absence | bm25 | mrr | 0.5000 | 1/170 | False |
| absence | bm25 | ndcg_at_k | 0.6309 | 1/144 | False |
| absence | bm25 | precision_at_k | 0.5000 | 1/170 | False |
| absence | bm25 | provenance_coverage | 1.0000 | 1/1 | True |
| absence | bm25 | recall_at_k | 1.0000 | 1/1 | True |
| absence | bm25 | scope_accuracy | 0.0000 | 1/48 | False |
| absence | bm25 | set_f1 | 0.6667 | 1/133 | False |
| absence | bm25 | stale_leak_rate | 1.0000 | 1/1 | True |
| absence | bm25 | supersession_accuracy | 0.0000 | 1/48 | False |
| absence | bm25 | unsupported_claim_rate | 0.0000 | 1/48 | False |
| absence | cortex | abstention_recall | 1.0000 | 1/1 | True |
| absence | cortex | answer_support_recall | 1.0000 | 1/1 | True |
| absence | cortex | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| absence | cortex | current_state_accuracy | 1.0000 | 1/1 | True |
| absence | cortex | deletion_compliance | 1.0000 | 1/1 | True |
| absence | cortex | evidence_resolution_rate | 1.0000 | 1/1 | True |
| absence | cortex | extraction_recall | 1.0000 | 1/1 | True |
| absence | cortex | extraction_spurious_rate | 0.5000 | 1/170 | False |
| absence | cortex | false_certainty_rate | 0.0000 | 1/48 | False |
| absence | cortex | lineage_completeness | 1.0000 | 1/1 | True |
| absence | cortex | mrr | 1.0000 | 1/1 | True |
| absence | cortex | ndcg_at_k | 1.0000 | 1/1 | True |
| absence | cortex | precision_at_k | 1.0000 | 1/1 | True |
| absence | cortex | provenance_coverage | 1.0000 | 1/1 | True |
| absence | cortex | recall_at_k | 1.0000 | 1/1 | True |
| absence | cortex | scope_accuracy | 1.0000 | 1/1 | True |
| absence | cortex | set_f1 | 1.0000 | 1/1 | True |
| absence | cortex | stale_leak_rate | 0.0000 | 1/48 | False |
| absence | cortex | supersession_accuracy | 1.0000 | 1/1 | True |
| absence | cortex | unsupported_claim_rate | 0.0000 | 1/48 | False |
| absence | no_memory | abstention_recall | 0.0000 | 1/48 | False |
| absence | no_memory | answer_support_recall | 0.0000 | 1/48 | False |
| absence | no_memory | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| absence | no_memory | current_state_accuracy | 0.0000 | 1/48 | False |
| absence | no_memory | deletion_compliance | 1.0000 | 1/1 | True |
| absence | no_memory | evidence_resolution_rate | 1.0000 | 1/1 | True |
| absence | no_memory | false_certainty_rate | 0.0000 | 1/48 | False |
| absence | no_memory | lineage_completeness | 0.0000 | 1/48 | False |
| absence | no_memory | mrr | 0.0000 | 1/48 | False |
| absence | no_memory | ndcg_at_k | 0.0000 | 1/48 | False |
| absence | no_memory | precision_at_k | 0.0000 | 1/48 | False |
| absence | no_memory | provenance_coverage | 0.0000 | 1/48 | False |
| absence | no_memory | recall_at_k | 0.0000 | 1/48 | False |
| absence | no_memory | scope_accuracy | 0.0000 | 1/48 | False |
| absence | no_memory | set_f1 | 0.0000 | 1/48 | False |
| absence | no_memory | stale_leak_rate | 0.0000 | 1/48 | False |
| absence | no_memory | supersession_accuracy | 1.0000 | 1/1 | True |
| absence | no_memory | unsupported_claim_rate | 0.0000 | 1/48 | False |
| absence | oracle | abstention_recall | 1.0000 | 1/1 | True |
| absence | oracle | answer_support_recall | 1.0000 | 1/1 | True |
| absence | oracle | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| absence | oracle | current_state_accuracy | 1.0000 | 1/1 | True |
| absence | oracle | deletion_compliance | 1.0000 | 1/1 | True |
| absence | oracle | evidence_resolution_rate | 1.0000 | 1/1 | True |
| absence | oracle | false_certainty_rate | 0.0000 | 1/48 | False |
| absence | oracle | lineage_completeness | 0.5000 | 1/170 | False |
| absence | oracle | mrr | 1.0000 | 1/1 | True |
| absence | oracle | ndcg_at_k | 1.0000 | 1/1 | True |
| absence | oracle | precision_at_k | 1.0000 | 1/1 | True |
| absence | oracle | provenance_coverage | 1.0000 | 1/1 | True |
| absence | oracle | recall_at_k | 1.0000 | 1/1 | True |
| absence | oracle | scope_accuracy | 1.0000 | 1/1 | True |
| absence | oracle | set_f1 | 1.0000 | 1/1 | True |
| absence | oracle | stale_leak_rate | 0.0000 | 1/48 | False |
| absence | oracle | supersession_accuracy | 1.0000 | 1/1 | True |
| absence | oracle | unsupported_claim_rate | 0.0000 | 1/48 | False |
| absence | raw_context | abstention_recall | 1.0000 | 1/1 | True |
| absence | raw_context | answer_support_recall | 1.0000 | 1/1 | True |
| absence | raw_context | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| absence | raw_context | current_state_accuracy | 1.0000 | 1/1 | True |
| absence | raw_context | deletion_compliance | 0.0000 | 1/48 | False |
| absence | raw_context | evidence_resolution_rate | 1.0000 | 1/1 | True |
| absence | raw_context | false_certainty_rate | 0.0000 | 1/48 | False |
| absence | raw_context | lineage_completeness | 1.0000 | 1/1 | True |
| absence | raw_context | mrr | 0.5000 | 1/170 | False |
| absence | raw_context | ndcg_at_k | 0.6309 | 1/144 | False |
| absence | raw_context | precision_at_k | 0.5000 | 1/170 | False |
| absence | raw_context | provenance_coverage | 1.0000 | 1/1 | True |
| absence | raw_context | recall_at_k | 1.0000 | 1/1 | True |
| absence | raw_context | scope_accuracy | 0.0000 | 1/48 | False |
| absence | raw_context | set_f1 | 0.6667 | 1/133 | False |
| absence | raw_context | stale_leak_rate | 1.0000 | 1/1 | True |
| absence | raw_context | supersession_accuracy | 0.0000 | 1/48 | False |
| absence | raw_context | unsupported_claim_rate | 0.0000 | 1/48 | False |
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
| deletion | bm25 | precision_at_k | 0.5000 | 1/170 | False |
| deletion | bm25 | provenance_coverage | 1.0000 | 1/1 | True |
| deletion | bm25 | recall_at_k | 1.0000 | 1/1 | True |
| deletion | bm25 | scope_accuracy | 0.0000 | 1/48 | False |
| deletion | bm25 | set_f1 | 0.6667 | 1/133 | False |
| deletion | bm25 | stale_leak_rate | 1.0000 | 1/1 | True |
| deletion | bm25 | supersession_accuracy | 0.0000 | 1/48 | False |
| deletion | bm25 | unsupported_claim_rate | 0.0000 | 1/48 | False |
| deletion | cortex | abstention_recall | 1.0000 | 1/1 | True |
| deletion | cortex | answer_support_recall | 1.0000 | 1/1 | True |
| deletion | cortex | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| deletion | cortex | current_state_accuracy | 1.0000 | 1/1 | True |
| deletion | cortex | deletion_compliance | 0.0000 | 1/48 | False |
| deletion | cortex | evidence_resolution_rate | 1.0000 | 1/1 | True |
| deletion | cortex | extraction_recall | 1.0000 | 1/1 | True |
| deletion | cortex | extraction_spurious_rate | 0.5000 | 1/170 | False |
| deletion | cortex | false_certainty_rate | 0.0000 | 1/48 | False |
| deletion | cortex | lineage_completeness | 0.0000 | 1/48 | False |
| deletion | cortex | mrr | 0.5000 | 1/170 | False |
| deletion | cortex | ndcg_at_k | 0.6309 | 1/144 | False |
| deletion | cortex | precision_at_k | 0.5000 | 1/170 | False |
| deletion | cortex | provenance_coverage | 1.0000 | 1/1 | True |
| deletion | cortex | recall_at_k | 1.0000 | 1/1 | True |
| deletion | cortex | scope_accuracy | 0.0000 | 1/48 | False |
| deletion | cortex | set_f1 | 0.6667 | 1/133 | False |
| deletion | cortex | stale_leak_rate | 1.0000 | 1/1 | True |
| deletion | cortex | supersession_accuracy | 0.0000 | 1/48 | False |
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
| deletion | raw_context | answer_support_recall | 1.0000 | 1/1 | True |
| deletion | raw_context | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| deletion | raw_context | current_state_accuracy | 1.0000 | 1/1 | True |
| deletion | raw_context | deletion_compliance | 0.0000 | 1/48 | False |
| deletion | raw_context | evidence_resolution_rate | 1.0000 | 1/1 | True |
| deletion | raw_context | false_certainty_rate | 0.0000 | 1/48 | False |
| deletion | raw_context | lineage_completeness | 1.0000 | 1/1 | True |
| deletion | raw_context | mrr | 0.5000 | 1/170 | False |
| deletion | raw_context | ndcg_at_k | 0.6309 | 1/144 | False |
| deletion | raw_context | precision_at_k | 0.5000 | 1/170 | False |
| deletion | raw_context | provenance_coverage | 1.0000 | 1/1 | True |
| deletion | raw_context | recall_at_k | 1.0000 | 1/1 | True |
| deletion | raw_context | scope_accuracy | 0.0000 | 1/48 | False |
| deletion | raw_context | set_f1 | 0.6667 | 1/133 | False |
| deletion | raw_context | stale_leak_rate | 1.0000 | 1/1 | True |
| deletion | raw_context | supersession_accuracy | 0.0000 | 1/48 | False |
| deletion | raw_context | unsupported_claim_rate | 0.0000 | 1/48 | False |
| exact_recall | bm25 | abstention_recall | 1.0000 | 1/1 | True |
| exact_recall | bm25 | answer_support_recall | 1.0000 | 1/1 | True |
| exact_recall | bm25 | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| exact_recall | bm25 | current_state_accuracy | 1.0000 | 1/1 | True |
| exact_recall | bm25 | deletion_compliance | 1.0000 | 1/1 | True |
| exact_recall | bm25 | evidence_resolution_rate | 1.0000 | 1/1 | True |
| exact_recall | bm25 | false_certainty_rate | 0.0000 | 1/48 | False |
| exact_recall | bm25 | lineage_completeness | 1.0000 | 1/1 | True |
| exact_recall | bm25 | mrr | 1.0000 | 1/1 | True |
| exact_recall | bm25 | ndcg_at_k | 1.0000 | 1/1 | True |
| exact_recall | bm25 | precision_at_k | 1.0000 | 1/1 | True |
| exact_recall | bm25 | provenance_coverage | 1.0000 | 1/1 | True |
| exact_recall | bm25 | recall_at_k | 1.0000 | 1/1 | True |
| exact_recall | bm25 | scope_accuracy | 1.0000 | 1/1 | True |
| exact_recall | bm25 | set_f1 | 1.0000 | 1/1 | True |
| exact_recall | bm25 | stale_leak_rate | 0.0000 | 1/48 | False |
| exact_recall | bm25 | supersession_accuracy | 1.0000 | 1/1 | True |
| exact_recall | bm25 | unsupported_claim_rate | 0.0000 | 1/48 | False |
| exact_recall | cortex | abstention_recall | 1.0000 | 1/1 | True |
| exact_recall | cortex | answer_support_recall | 1.0000 | 1/1 | True |
| exact_recall | cortex | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| exact_recall | cortex | current_state_accuracy | 1.0000 | 1/1 | True |
| exact_recall | cortex | deletion_compliance | 1.0000 | 1/1 | True |
| exact_recall | cortex | evidence_resolution_rate | 1.0000 | 1/1 | True |
| exact_recall | cortex | extraction_recall | 1.0000 | 1/1 | True |
| exact_recall | cortex | extraction_spurious_rate | 0.0000 | 1/48 | False |
| exact_recall | cortex | false_certainty_rate | 0.0000 | 1/48 | False |
| exact_recall | cortex | lineage_completeness | 1.0000 | 1/1 | True |
| exact_recall | cortex | mrr | 1.0000 | 1/1 | True |
| exact_recall | cortex | ndcg_at_k | 1.0000 | 1/1 | True |
| exact_recall | cortex | precision_at_k | 1.0000 | 1/1 | True |
| exact_recall | cortex | provenance_coverage | 1.0000 | 1/1 | True |
| exact_recall | cortex | recall_at_k | 1.0000 | 1/1 | True |
| exact_recall | cortex | scope_accuracy | 1.0000 | 1/1 | True |
| exact_recall | cortex | set_f1 | 1.0000 | 1/1 | True |
| exact_recall | cortex | stale_leak_rate | 0.0000 | 1/48 | False |
| exact_recall | cortex | supersession_accuracy | 1.0000 | 1/1 | True |
| exact_recall | cortex | unsupported_claim_rate | 0.0000 | 1/48 | False |
| exact_recall | no_memory | abstention_recall | 0.0000 | 1/48 | False |
| exact_recall | no_memory | answer_support_recall | 0.0000 | 1/48 | False |
| exact_recall | no_memory | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| exact_recall | no_memory | current_state_accuracy | 0.0000 | 1/48 | False |
| exact_recall | no_memory | deletion_compliance | 1.0000 | 1/1 | True |
| exact_recall | no_memory | evidence_resolution_rate | 1.0000 | 1/1 | True |
| exact_recall | no_memory | false_certainty_rate | 0.0000 | 1/48 | False |
| exact_recall | no_memory | lineage_completeness | 1.0000 | 1/1 | True |
| exact_recall | no_memory | mrr | 0.0000 | 1/48 | False |
| exact_recall | no_memory | ndcg_at_k | 0.0000 | 1/48 | False |
| exact_recall | no_memory | precision_at_k | 0.0000 | 1/48 | False |
| exact_recall | no_memory | provenance_coverage | 0.0000 | 1/48 | False |
| exact_recall | no_memory | recall_at_k | 0.0000 | 1/48 | False |
| exact_recall | no_memory | scope_accuracy | 0.0000 | 1/48 | False |
| exact_recall | no_memory | set_f1 | 0.0000 | 1/48 | False |
| exact_recall | no_memory | stale_leak_rate | 0.0000 | 1/48 | False |
| exact_recall | no_memory | supersession_accuracy | 1.0000 | 1/1 | True |
| exact_recall | no_memory | unsupported_claim_rate | 0.0000 | 1/48 | False |
| exact_recall | oracle | abstention_recall | 1.0000 | 1/1 | True |
| exact_recall | oracle | answer_support_recall | 1.0000 | 1/1 | True |
| exact_recall | oracle | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| exact_recall | oracle | current_state_accuracy | 1.0000 | 1/1 | True |
| exact_recall | oracle | deletion_compliance | 1.0000 | 1/1 | True |
| exact_recall | oracle | evidence_resolution_rate | 1.0000 | 1/1 | True |
| exact_recall | oracle | false_certainty_rate | 0.0000 | 1/48 | False |
| exact_recall | oracle | lineage_completeness | 1.0000 | 1/1 | True |
| exact_recall | oracle | mrr | 1.0000 | 1/1 | True |
| exact_recall | oracle | ndcg_at_k | 1.0000 | 1/1 | True |
| exact_recall | oracle | precision_at_k | 1.0000 | 1/1 | True |
| exact_recall | oracle | provenance_coverage | 1.0000 | 1/1 | True |
| exact_recall | oracle | recall_at_k | 1.0000 | 1/1 | True |
| exact_recall | oracle | scope_accuracy | 1.0000 | 1/1 | True |
| exact_recall | oracle | set_f1 | 1.0000 | 1/1 | True |
| exact_recall | oracle | stale_leak_rate | 0.0000 | 1/48 | False |
| exact_recall | oracle | supersession_accuracy | 1.0000 | 1/1 | True |
| exact_recall | oracle | unsupported_claim_rate | 0.0000 | 1/48 | False |
| exact_recall | raw_context | abstention_recall | 1.0000 | 1/1 | True |
| exact_recall | raw_context | answer_support_recall | 1.0000 | 1/1 | True |
| exact_recall | raw_context | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| exact_recall | raw_context | current_state_accuracy | 1.0000 | 1/1 | True |
| exact_recall | raw_context | deletion_compliance | 1.0000 | 1/1 | True |
| exact_recall | raw_context | evidence_resolution_rate | 1.0000 | 1/1 | True |
| exact_recall | raw_context | false_certainty_rate | 0.0000 | 1/48 | False |
| exact_recall | raw_context | lineage_completeness | 1.0000 | 1/1 | True |
| exact_recall | raw_context | mrr | 1.0000 | 1/1 | True |
| exact_recall | raw_context | ndcg_at_k | 1.0000 | 1/1 | True |
| exact_recall | raw_context | precision_at_k | 1.0000 | 1/1 | True |
| exact_recall | raw_context | provenance_coverage | 1.0000 | 1/1 | True |
| exact_recall | raw_context | recall_at_k | 1.0000 | 1/1 | True |
| exact_recall | raw_context | scope_accuracy | 1.0000 | 1/1 | True |
| exact_recall | raw_context | set_f1 | 1.0000 | 1/1 | True |
| exact_recall | raw_context | stale_leak_rate | 0.0000 | 1/48 | False |
| exact_recall | raw_context | supersession_accuracy | 1.0000 | 1/1 | True |
| exact_recall | raw_context | unsupported_claim_rate | 0.0000 | 1/48 | False |
| tracking | bm25 | abstention_recall | 1.0000 | 1/1 | True |
| tracking | bm25 | answer_support_recall | 1.0000 | 1/1 | True |
| tracking | bm25 | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| tracking | bm25 | current_state_accuracy | 1.0000 | 1/1 | True |
| tracking | bm25 | deletion_compliance | 0.0000 | 1/48 | False |
| tracking | bm25 | evidence_resolution_rate | 1.0000 | 1/1 | True |
| tracking | bm25 | false_certainty_rate | 0.0000 | 1/48 | False |
| tracking | bm25 | lineage_completeness | 1.0000 | 1/1 | True |
| tracking | bm25 | mrr | 0.5000 | 1/170 | False |
| tracking | bm25 | ndcg_at_k | 0.6309 | 1/144 | False |
| tracking | bm25 | precision_at_k | 0.5000 | 1/170 | False |
| tracking | bm25 | provenance_coverage | 1.0000 | 1/1 | True |
| tracking | bm25 | recall_at_k | 1.0000 | 1/1 | True |
| tracking | bm25 | scope_accuracy | 0.0000 | 1/48 | False |
| tracking | bm25 | set_f1 | 0.6667 | 1/133 | False |
| tracking | bm25 | stale_leak_rate | 1.0000 | 1/1 | True |
| tracking | bm25 | supersession_accuracy | 0.0000 | 1/48 | False |
| tracking | bm25 | unsupported_claim_rate | 0.0000 | 1/48 | False |
| tracking | cortex | abstention_recall | 1.0000 | 1/1 | True |
| tracking | cortex | answer_support_recall | 1.0000 | 1/1 | True |
| tracking | cortex | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| tracking | cortex | current_state_accuracy | 1.0000 | 1/1 | True |
| tracking | cortex | deletion_compliance | 1.0000 | 1/1 | True |
| tracking | cortex | evidence_resolution_rate | 1.0000 | 1/1 | True |
| tracking | cortex | extraction_recall | 1.0000 | 1/1 | True |
| tracking | cortex | extraction_spurious_rate | 0.5000 | 1/170 | False |
| tracking | cortex | false_certainty_rate | 0.0000 | 1/48 | False |
| tracking | cortex | lineage_completeness | 1.0000 | 1/1 | True |
| tracking | cortex | mrr | 1.0000 | 1/1 | True |
| tracking | cortex | ndcg_at_k | 1.0000 | 1/1 | True |
| tracking | cortex | precision_at_k | 1.0000 | 1/1 | True |
| tracking | cortex | provenance_coverage | 1.0000 | 1/1 | True |
| tracking | cortex | recall_at_k | 1.0000 | 1/1 | True |
| tracking | cortex | scope_accuracy | 1.0000 | 1/1 | True |
| tracking | cortex | set_f1 | 1.0000 | 1/1 | True |
| tracking | cortex | stale_leak_rate | 0.0000 | 1/48 | False |
| tracking | cortex | supersession_accuracy | 1.0000 | 1/1 | True |
| tracking | cortex | unsupported_claim_rate | 0.0000 | 1/48 | False |
| tracking | no_memory | abstention_recall | 0.0000 | 1/48 | False |
| tracking | no_memory | answer_support_recall | 0.0000 | 1/48 | False |
| tracking | no_memory | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| tracking | no_memory | current_state_accuracy | 0.0000 | 1/48 | False |
| tracking | no_memory | deletion_compliance | 1.0000 | 1/1 | True |
| tracking | no_memory | evidence_resolution_rate | 1.0000 | 1/1 | True |
| tracking | no_memory | false_certainty_rate | 0.0000 | 1/48 | False |
| tracking | no_memory | lineage_completeness | 0.0000 | 1/48 | False |
| tracking | no_memory | mrr | 0.0000 | 1/48 | False |
| tracking | no_memory | ndcg_at_k | 0.0000 | 1/48 | False |
| tracking | no_memory | precision_at_k | 0.0000 | 1/48 | False |
| tracking | no_memory | provenance_coverage | 0.0000 | 1/48 | False |
| tracking | no_memory | recall_at_k | 0.0000 | 1/48 | False |
| tracking | no_memory | scope_accuracy | 0.0000 | 1/48 | False |
| tracking | no_memory | set_f1 | 0.0000 | 1/48 | False |
| tracking | no_memory | stale_leak_rate | 0.0000 | 1/48 | False |
| tracking | no_memory | supersession_accuracy | 1.0000 | 1/1 | True |
| tracking | no_memory | unsupported_claim_rate | 0.0000 | 1/48 | False |
| tracking | oracle | abstention_recall | 1.0000 | 1/1 | True |
| tracking | oracle | answer_support_recall | 1.0000 | 1/1 | True |
| tracking | oracle | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| tracking | oracle | current_state_accuracy | 1.0000 | 1/1 | True |
| tracking | oracle | deletion_compliance | 1.0000 | 1/1 | True |
| tracking | oracle | evidence_resolution_rate | 1.0000 | 1/1 | True |
| tracking | oracle | false_certainty_rate | 0.0000 | 1/48 | False |
| tracking | oracle | lineage_completeness | 0.5000 | 1/170 | False |
| tracking | oracle | mrr | 1.0000 | 1/1 | True |
| tracking | oracle | ndcg_at_k | 1.0000 | 1/1 | True |
| tracking | oracle | precision_at_k | 1.0000 | 1/1 | True |
| tracking | oracle | provenance_coverage | 1.0000 | 1/1 | True |
| tracking | oracle | recall_at_k | 1.0000 | 1/1 | True |
| tracking | oracle | scope_accuracy | 1.0000 | 1/1 | True |
| tracking | oracle | set_f1 | 1.0000 | 1/1 | True |
| tracking | oracle | stale_leak_rate | 0.0000 | 1/48 | False |
| tracking | oracle | supersession_accuracy | 1.0000 | 1/1 | True |
| tracking | oracle | unsupported_claim_rate | 0.0000 | 1/48 | False |
| tracking | raw_context | abstention_recall | 1.0000 | 1/1 | True |
| tracking | raw_context | answer_support_recall | 1.0000 | 1/1 | True |
| tracking | raw_context | contradiction_exposure_rate | 0.0000 | 1/48 | False |
| tracking | raw_context | current_state_accuracy | 1.0000 | 1/1 | True |
| tracking | raw_context | deletion_compliance | 0.0000 | 1/48 | False |
| tracking | raw_context | evidence_resolution_rate | 1.0000 | 1/1 | True |
| tracking | raw_context | false_certainty_rate | 0.0000 | 1/48 | False |
| tracking | raw_context | lineage_completeness | 1.0000 | 1/1 | True |
| tracking | raw_context | mrr | 0.5000 | 1/170 | False |
| tracking | raw_context | ndcg_at_k | 0.6309 | 1/144 | False |
| tracking | raw_context | precision_at_k | 0.5000 | 1/170 | False |
| tracking | raw_context | provenance_coverage | 1.0000 | 1/1 | True |
| tracking | raw_context | recall_at_k | 1.0000 | 1/1 | True |
| tracking | raw_context | scope_accuracy | 0.0000 | 1/48 | False |
| tracking | raw_context | set_f1 | 0.6667 | 1/133 | False |
| tracking | raw_context | stale_leak_rate | 1.0000 | 1/1 | True |
| tracking | raw_context | supersession_accuracy | 0.0000 | 1/48 | False |
| tracking | raw_context | unsupported_claim_rate | 0.0000 | 1/48 | False |

## Estratificação da amostra (plano §9.1)

Contagem de casos únicos por eixo — uma média única nunca revela se a amostra está concentrada em um hop, tamanho de histórico ou carga de filler.

| Eixo | Bucket | n (casos) |
|---|---|---:|
| task_type | absence | 1 |
| task_type | deletion | 1 |
| task_type | exact_recall | 1 |
| task_type | tracking | 1 |
| hop | 0 | 2 |
| hop | 1 | 2 |
| history_size | s | 3 |
| history_size | xs | 1 |
| filler | nofiller | 4 |

## Comparação pareada (cortex − baseline)

MDE pré-registrado: 0.15. Confirmatório exige n ≥ `required_n`. `holm` marca rejeição após correção dentro da família.

| Métrica | Baseline | n | req n | diff | IC95 | p | holm |
|---|---|---:|---:|---:|---|---:|---|
| cortex_vs_bm25 | abstention_recall | 4 | 1 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_raw_context | abstention_recall | 4 | 1 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_no_memory | abstention_recall | 4 | 48 | +1.0000 | [+1.0000, +1.0000] | 0.0005 | True |
| cortex_vs_bm25 | answer_support_recall | 4 | 1 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_raw_context | answer_support_recall | 4 | 1 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_no_memory | answer_support_recall | 4 | 48 | +1.0000 | [+1.0000, +1.0000] | 0.0005 | True |
| cortex_vs_bm25 | contradiction_exposure_rate | 4 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_raw_context | contradiction_exposure_rate | 4 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_no_memory | contradiction_exposure_rate | 4 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_bm25 | current_state_accuracy | 4 | 1 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_raw_context | current_state_accuracy | 4 | 1 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_no_memory | current_state_accuracy | 4 | 48 | +1.0000 | [+1.0000, +1.0000] | 0.0005 | True |
| cortex_vs_bm25 | deletion_compliance | 4 | 152 | +0.5000 | [+0.0000, +1.0000] | 0.1190 | False |
| cortex_vs_raw_context | deletion_compliance | 4 | 152 | +0.5000 | [+0.0000, +1.0000] | 0.1190 | False |
| cortex_vs_no_memory | deletion_compliance | 4 | 1 | -0.2500 | [-0.7500, +0.0000] | 0.5665 | False |
| cortex_vs_bm25 | evidence_resolution_rate | 4 | 1 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_raw_context | evidence_resolution_rate | 4 | 1 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_no_memory | evidence_resolution_rate | 4 | 1 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_bm25 | false_certainty_rate | 4 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_raw_context | false_certainty_rate | 4 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_no_memory | false_certainty_rate | 4 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_bm25 | lineage_completeness | 4 | 1 | -0.2500 | [-0.7500, +0.0000] | 0.5665 | False |
| cortex_vs_raw_context | lineage_completeness | 4 | 1 | -0.2500 | [-0.7500, +0.0000] | 0.5665 | False |
| cortex_vs_no_memory | lineage_completeness | 4 | 152 | +0.5000 | [+0.0000, +1.0000] | 0.1190 | False |
| cortex_vs_bm25 | mrr | 4 | 146 | +0.2500 | [+0.0000, +0.5000] | 0.1190 | False |
| cortex_vs_raw_context | mrr | 4 | 146 | +0.2500 | [+0.0000, +0.5000] | 0.1190 | False |
| cortex_vs_no_memory | mrr | 4 | 48 | +0.8750 | [+0.6250, +1.0000] | 0.0005 | True |
| cortex_vs_bm25 | ndcg_at_k | 4 | 112 | +0.1845 | [+0.0000, +0.3691] | 0.1190 | False |
| cortex_vs_raw_context | ndcg_at_k | 4 | 112 | +0.1845 | [+0.0000, +0.3691] | 0.1190 | False |
| cortex_vs_no_memory | ndcg_at_k | 4 | 48 | +0.9077 | [+0.7232, +1.0000] | 0.0005 | True |
| cortex_vs_bm25 | precision_at_k | 4 | 146 | +0.2500 | [+0.0000, +0.5000] | 0.1190 | False |
| cortex_vs_raw_context | precision_at_k | 4 | 146 | +0.2500 | [+0.0000, +0.5000] | 0.1190 | False |
| cortex_vs_no_memory | precision_at_k | 4 | 48 | +0.8750 | [+0.6250, +1.0000] | 0.0005 | True |
| cortex_vs_bm25 | provenance_coverage | 4 | 1 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_raw_context | provenance_coverage | 4 | 1 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_no_memory | provenance_coverage | 4 | 48 | +1.0000 | [+1.0000, +1.0000] | 0.0005 | True |
| cortex_vs_bm25 | recall_at_k | 4 | 1 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_raw_context | recall_at_k | 4 | 1 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_no_memory | recall_at_k | 4 | 48 | +1.0000 | [+1.0000, +1.0000] | 0.0005 | True |
| cortex_vs_bm25 | scope_accuracy | 4 | 152 | +0.5000 | [+0.0000, +1.0000] | 0.1190 | False |
| cortex_vs_raw_context | scope_accuracy | 4 | 152 | +0.5000 | [+0.0000, +1.0000] | 0.1190 | False |
| cortex_vs_no_memory | scope_accuracy | 4 | 48 | +0.7500 | [+0.2500, +1.0000] | 0.0040 | False |
| cortex_vs_bm25 | set_f1 | 4 | 100 | +0.1667 | [+0.0000, +0.3333] | 0.1190 | False |
| cortex_vs_raw_context | set_f1 | 4 | 100 | +0.1667 | [+0.0000, +0.3333] | 0.1190 | False |
| cortex_vs_no_memory | set_f1 | 4 | 48 | +0.9167 | [+0.7500, +1.0000] | 0.0005 | True |
| cortex_vs_bm25 | stale_leak_rate | 4 | 100 | -0.5000 | [-1.0000, +0.0000] | 0.1190 | False |
| cortex_vs_raw_context | stale_leak_rate | 4 | 100 | -0.5000 | [-1.0000, +0.0000] | 0.1190 | False |
| cortex_vs_no_memory | stale_leak_rate | 4 | 48 | +0.2500 | [+0.0000, +0.7500] | 0.5665 | False |
| cortex_vs_bm25 | supersession_accuracy | 4 | 152 | +0.5000 | [+0.0000, +1.0000] | 0.1190 | False |
| cortex_vs_raw_context | supersession_accuracy | 4 | 152 | +0.5000 | [+0.0000, +1.0000] | 0.1190 | False |
| cortex_vs_no_memory | supersession_accuracy | 4 | 1 | -0.2500 | [-0.7500, +0.0000] | 0.5665 | False |
| cortex_vs_bm25 | unsupported_claim_rate | 4 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_raw_context | unsupported_claim_rate | 4 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_no_memory | unsupported_claim_rate | 4 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |

### Correção de múltiplas hipóteses (Holm-Bonferroni, por família)

| Família | Comparações | Rejeitadas | menor p | maior p |
|---|---:|---:|---:|---:|
| abstention | 6 | 1 | 0.0005 | 1.0000 |
| evidence | 9 | 1 | 0.0005 | 1.0000 |
| retrieval | 21 | 6 | 0.0005 | 1.0000 |
| temporality | 18 | 1 | 0.0005 | 1.0000 |

## Gates

### G0_reproducibility
- explicit_errors: 0
- leakage_events: 0
- clean: True

### G1_cortex_integrity
- stale_leak_rate_cortex: 0.25
- stale_leak_rate_bm25: 0.75
- stale_leak_rate_raw_context: 0.75
- stale_leak_not_worse_than_bm25: True
- stale_leak_not_worse_than_raw_context: True
- paired_interval_available: True
- exceptions_converted_to_zero: 0

### G2_relative_value
- set_f1: {'comparison': 'cortex_vs_raw_context', 'holm_significant': False, 'n': 4, 'diff': 0.166666665, 'ci_low': 0.0, 'ci_high': 0.33333333, 'ci_includes_zero': True, 'family': 'retrieval', 'required_n': 100, 'minimum_detectable_effect': 0.15, 'power_basis': 'baseline_arm', 'p_value': 0.119, 'confirmatory': False}
- current_state_accuracy: {'comparison': 'cortex_vs_bm25', 'holm_significant': False, 'n': 4, 'diff': 0.0, 'ci_low': 0.0, 'ci_high': 0.0, 'ci_includes_zero': True, 'family': 'temporality', 'required_n': 1, 'minimum_detectable_effect': 0.15, 'power_basis': 'baseline_arm', 'p_value': 1.0, 'confirmatory': True}
- deletion_compliance: {'comparison': 'cortex_vs_bm25', 'holm_significant': False, 'n': 4, 'diff': 0.5, 'ci_low': 0.0, 'ci_high': 1.0, 'ci_includes_zero': True, 'family': 'temporality', 'required_n': 152, 'minimum_detectable_effect': 0.15, 'power_basis': 'baseline_arm', 'p_value': 0.119, 'confirmatory': False}
- abstention_recall: {'comparison': 'cortex_vs_bm25', 'holm_significant': False, 'n': 4, 'diff': 0.0, 'ci_low': 0.0, 'ci_high': 0.0, 'ci_includes_zero': True, 'family': 'abstention', 'required_n': 1, 'minimum_detectable_effect': 0.15, 'power_basis': 'baseline_arm', 'p_value': 1.0, 'confirmatory': True}
- recall_at_k: {'comparison': 'cortex_vs_bm25', 'holm_significant': False, 'n': 4, 'diff': 0.0, 'ci_low': 0.0, 'ci_high': 0.0, 'ci_includes_zero': True, 'family': 'retrieval', 'required_n': 1, 'minimum_detectable_effect': 0.15, 'power_basis': 'baseline_arm', 'p_value': 1.0, 'confirmatory': True}

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

`recalibrar`

Decisões possíveis (plano §17): promover, recalibrar, reduzir_claim, bloquear_expansao.
Uma média única nunca é o resultado final; ver `summary.json` por task type e split.
