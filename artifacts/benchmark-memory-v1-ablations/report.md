# Cortex memory benchmark v1

- Corpus: `sha256:2adb4efba087fe716d7f51db2622b5724a2d3d07d023d70258f5f6a02cbe58b9`
- Revisões: `{"internal": "engineering-memory-v2"}`

## Endpoints por task type

| Task type | Adapter | Endpoint | Mean | n / req n | Confirmatório |
|---|---|---|---:|---|---|
| absence | bm25 | abstention_recall | 0.0000 | 42/48 | False |
| absence | bm25 | answer_support_recall | 0.0000 | 42/48 | False |
| absence | bm25 | contradiction_exposure_rate | 0.0000 | 42/48 | False |
| absence | bm25 | current_state_accuracy | 1.0000 | 42/1 | True |
| absence | bm25 | deletion_compliance | 1.0000 | 42/1 | True |
| absence | bm25 | evidence_resolution_rate | 1.0000 | 42/1 | True |
| absence | bm25 | false_certainty_rate | 0.0000 | 42/48 | False |
| absence | bm25 | lineage_completeness | 1.0000 | 42/1 | True |
| absence | bm25 | mrr | 0.0000 | 42/48 | False |
| absence | bm25 | ndcg_at_k | 0.0000 | 42/48 | False |
| absence | bm25 | precision_at_k | 0.0000 | 42/48 | False |
| absence | bm25 | provenance_coverage | 1.0000 | 42/1 | True |
| absence | bm25 | recall_at_k | 0.0000 | 42/48 | False |
| absence | bm25 | scope_accuracy | 0.9524 | 42/17 | True |
| absence | bm25 | set_f1 | 0.9524 | 42/17 | True |
| absence | bm25 | stale_leak_rate | 0.0000 | 42/48 | False |
| absence | bm25 | supersession_accuracy | 1.0000 | 42/1 | True |
| absence | bm25 | unsupported_claim_rate | 0.0000 | 42/48 | False |
| absence | cortex | abstention_recall | 1.0000 | 42/1 | True |
| absence | cortex | answer_support_recall | 0.0000 | 42/48 | False |
| absence | cortex | contradiction_exposure_rate | 0.0000 | 42/48 | False |
| absence | cortex | current_state_accuracy | 1.0000 | 42/1 | True |
| absence | cortex | deletion_compliance | 1.0000 | 42/1 | True |
| absence | cortex | evidence_resolution_rate | 1.0000 | 42/1 | True |
| absence | cortex | extraction_recall | 1.0000 | 42/1 | True |
| absence | cortex | extraction_spurious_rate | 1.0000 | 42/1 | True |
| absence | cortex | false_certainty_rate | 0.0000 | 42/48 | False |
| absence | cortex | lineage_completeness | 1.0000 | 42/1 | True |
| absence | cortex | mrr | 0.0000 | 42/48 | False |
| absence | cortex | ndcg_at_k | 0.0000 | 42/48 | False |
| absence | cortex | precision_at_k | 0.0000 | 42/48 | False |
| absence | cortex | provenance_coverage | 1.0000 | 42/1 | True |
| absence | cortex | recall_at_k | 0.0000 | 42/48 | False |
| absence | cortex | scope_accuracy | 1.0000 | 42/1 | True |
| absence | cortex | set_f1 | 1.0000 | 42/1 | True |
| absence | cortex | stale_leak_rate | 0.0000 | 42/48 | False |
| absence | cortex | supersession_accuracy | 1.0000 | 42/1 | True |
| absence | cortex | unsupported_claim_rate | 0.0000 | 42/48 | False |
| absence | cortex[disable_authority] | abstention_recall | 1.0000 | 42/1 | True |
| absence | cortex[disable_authority] | answer_support_recall | 0.0000 | 42/48 | False |
| absence | cortex[disable_authority] | contradiction_exposure_rate | 0.0000 | 42/48 | False |
| absence | cortex[disable_authority] | current_state_accuracy | 1.0000 | 42/1 | True |
| absence | cortex[disable_authority] | deletion_compliance | 1.0000 | 42/1 | True |
| absence | cortex[disable_authority] | evidence_resolution_rate | 1.0000 | 42/1 | True |
| absence | cortex[disable_authority] | extraction_recall | 1.0000 | 42/1 | True |
| absence | cortex[disable_authority] | extraction_spurious_rate | 1.0000 | 42/1 | True |
| absence | cortex[disable_authority] | false_certainty_rate | 0.0000 | 42/48 | False |
| absence | cortex[disable_authority] | lineage_completeness | 1.0000 | 42/1 | True |
| absence | cortex[disable_authority] | mrr | 0.0000 | 42/48 | False |
| absence | cortex[disable_authority] | ndcg_at_k | 0.0000 | 42/48 | False |
| absence | cortex[disable_authority] | precision_at_k | 0.0000 | 42/48 | False |
| absence | cortex[disable_authority] | provenance_coverage | 1.0000 | 42/1 | True |
| absence | cortex[disable_authority] | recall_at_k | 0.0000 | 42/48 | False |
| absence | cortex[disable_authority] | scope_accuracy | 1.0000 | 42/1 | True |
| absence | cortex[disable_authority] | set_f1 | 1.0000 | 42/1 | True |
| absence | cortex[disable_authority] | stale_leak_rate | 0.0000 | 42/48 | False |
| absence | cortex[disable_authority] | supersession_accuracy | 1.0000 | 42/1 | True |
| absence | cortex[disable_authority] | unsupported_claim_rate | 0.0000 | 42/48 | False |
| absence | cortex[disable_contradiction_penalty] | abstention_recall | 1.0000 | 42/1 | True |
| absence | cortex[disable_contradiction_penalty] | answer_support_recall | 0.0000 | 42/48 | False |
| absence | cortex[disable_contradiction_penalty] | contradiction_exposure_rate | 0.0000 | 42/48 | False |
| absence | cortex[disable_contradiction_penalty] | current_state_accuracy | 1.0000 | 42/1 | True |
| absence | cortex[disable_contradiction_penalty] | deletion_compliance | 1.0000 | 42/1 | True |
| absence | cortex[disable_contradiction_penalty] | evidence_resolution_rate | 1.0000 | 42/1 | True |
| absence | cortex[disable_contradiction_penalty] | extraction_recall | 1.0000 | 42/1 | True |
| absence | cortex[disable_contradiction_penalty] | extraction_spurious_rate | 1.0000 | 42/1 | True |
| absence | cortex[disable_contradiction_penalty] | false_certainty_rate | 0.0000 | 42/48 | False |
| absence | cortex[disable_contradiction_penalty] | lineage_completeness | 1.0000 | 42/1 | True |
| absence | cortex[disable_contradiction_penalty] | mrr | 0.0000 | 42/48 | False |
| absence | cortex[disable_contradiction_penalty] | ndcg_at_k | 0.0000 | 42/48 | False |
| absence | cortex[disable_contradiction_penalty] | precision_at_k | 0.0000 | 42/48 | False |
| absence | cortex[disable_contradiction_penalty] | provenance_coverage | 1.0000 | 42/1 | True |
| absence | cortex[disable_contradiction_penalty] | recall_at_k | 0.0000 | 42/48 | False |
| absence | cortex[disable_contradiction_penalty] | scope_accuracy | 1.0000 | 42/1 | True |
| absence | cortex[disable_contradiction_penalty] | set_f1 | 1.0000 | 42/1 | True |
| absence | cortex[disable_contradiction_penalty] | stale_leak_rate | 0.0000 | 42/48 | False |
| absence | cortex[disable_contradiction_penalty] | supersession_accuracy | 1.0000 | 42/1 | True |
| absence | cortex[disable_contradiction_penalty] | unsupported_claim_rate | 0.0000 | 42/48 | False |
| absence | cortex[disable_dense] | abstention_recall | 1.0000 | 42/1 | True |
| absence | cortex[disable_dense] | answer_support_recall | 0.0000 | 42/48 | False |
| absence | cortex[disable_dense] | contradiction_exposure_rate | 0.0000 | 42/48 | False |
| absence | cortex[disable_dense] | current_state_accuracy | 1.0000 | 42/1 | True |
| absence | cortex[disable_dense] | deletion_compliance | 1.0000 | 42/1 | True |
| absence | cortex[disable_dense] | evidence_resolution_rate | 1.0000 | 42/1 | True |
| absence | cortex[disable_dense] | extraction_recall | 1.0000 | 42/1 | True |
| absence | cortex[disable_dense] | extraction_spurious_rate | 1.0000 | 42/1 | True |
| absence | cortex[disable_dense] | false_certainty_rate | 0.0000 | 42/48 | False |
| absence | cortex[disable_dense] | lineage_completeness | 1.0000 | 42/1 | True |
| absence | cortex[disable_dense] | mrr | 0.0000 | 42/48 | False |
| absence | cortex[disable_dense] | ndcg_at_k | 0.0000 | 42/48 | False |
| absence | cortex[disable_dense] | precision_at_k | 0.0000 | 42/48 | False |
| absence | cortex[disable_dense] | provenance_coverage | 1.0000 | 42/1 | True |
| absence | cortex[disable_dense] | recall_at_k | 0.0000 | 42/48 | False |
| absence | cortex[disable_dense] | scope_accuracy | 1.0000 | 42/1 | True |
| absence | cortex[disable_dense] | set_f1 | 1.0000 | 42/1 | True |
| absence | cortex[disable_dense] | stale_leak_rate | 0.0000 | 42/48 | False |
| absence | cortex[disable_dense] | supersession_accuracy | 1.0000 | 42/1 | True |
| absence | cortex[disable_dense] | unsupported_claim_rate | 0.0000 | 42/48 | False |
| absence | cortex[disable_evidence_ledger] | abstention_recall | 1.0000 | 42/1 | True |
| absence | cortex[disable_evidence_ledger] | answer_support_recall | 0.0000 | 42/48 | False |
| absence | cortex[disable_evidence_ledger] | contradiction_exposure_rate | 0.0000 | 42/48 | False |
| absence | cortex[disable_evidence_ledger] | current_state_accuracy | 1.0000 | 42/1 | True |
| absence | cortex[disable_evidence_ledger] | deletion_compliance | 1.0000 | 42/1 | True |
| absence | cortex[disable_evidence_ledger] | evidence_resolution_rate | 1.0000 | 42/1 | True |
| absence | cortex[disable_evidence_ledger] | extraction_recall | 1.0000 | 42/1 | True |
| absence | cortex[disable_evidence_ledger] | extraction_spurious_rate | 1.0000 | 42/1 | True |
| absence | cortex[disable_evidence_ledger] | false_certainty_rate | 0.0000 | 42/48 | False |
| absence | cortex[disable_evidence_ledger] | lineage_completeness | 1.0000 | 42/1 | True |
| absence | cortex[disable_evidence_ledger] | mrr | 0.0000 | 42/48 | False |
| absence | cortex[disable_evidence_ledger] | ndcg_at_k | 0.0000 | 42/48 | False |
| absence | cortex[disable_evidence_ledger] | precision_at_k | 0.0000 | 42/48 | False |
| absence | cortex[disable_evidence_ledger] | provenance_coverage | 1.0000 | 42/1 | True |
| absence | cortex[disable_evidence_ledger] | recall_at_k | 0.0000 | 42/48 | False |
| absence | cortex[disable_evidence_ledger] | scope_accuracy | 1.0000 | 42/1 | True |
| absence | cortex[disable_evidence_ledger] | set_f1 | 1.0000 | 42/1 | True |
| absence | cortex[disable_evidence_ledger] | stale_leak_rate | 0.0000 | 42/48 | False |
| absence | cortex[disable_evidence_ledger] | supersession_accuracy | 1.0000 | 42/1 | True |
| absence | cortex[disable_evidence_ledger] | unsupported_claim_rate | 0.0000 | 42/48 | False |
| absence | cortex[disable_graph_density] | abstention_recall | 1.0000 | 42/1 | True |
| absence | cortex[disable_graph_density] | answer_support_recall | 0.0000 | 42/48 | False |
| absence | cortex[disable_graph_density] | contradiction_exposure_rate | 0.0000 | 42/48 | False |
| absence | cortex[disable_graph_density] | current_state_accuracy | 1.0000 | 42/1 | True |
| absence | cortex[disable_graph_density] | deletion_compliance | 1.0000 | 42/1 | True |
| absence | cortex[disable_graph_density] | evidence_resolution_rate | 1.0000 | 42/1 | True |
| absence | cortex[disable_graph_density] | extraction_recall | 1.0000 | 42/1 | True |
| absence | cortex[disable_graph_density] | extraction_spurious_rate | 1.0000 | 42/1 | True |
| absence | cortex[disable_graph_density] | false_certainty_rate | 0.0000 | 42/48 | False |
| absence | cortex[disable_graph_density] | lineage_completeness | 1.0000 | 42/1 | True |
| absence | cortex[disable_graph_density] | mrr | 0.0000 | 42/48 | False |
| absence | cortex[disable_graph_density] | ndcg_at_k | 0.0000 | 42/48 | False |
| absence | cortex[disable_graph_density] | precision_at_k | 0.0000 | 42/48 | False |
| absence | cortex[disable_graph_density] | provenance_coverage | 1.0000 | 42/1 | True |
| absence | cortex[disable_graph_density] | recall_at_k | 0.0000 | 42/48 | False |
| absence | cortex[disable_graph_density] | scope_accuracy | 1.0000 | 42/1 | True |
| absence | cortex[disable_graph_density] | set_f1 | 1.0000 | 42/1 | True |
| absence | cortex[disable_graph_density] | stale_leak_rate | 0.0000 | 42/48 | False |
| absence | cortex[disable_graph_density] | supersession_accuracy | 1.0000 | 42/1 | True |
| absence | cortex[disable_graph_density] | unsupported_claim_rate | 0.0000 | 42/48 | False |
| absence | cortex[disable_supersession] | abstention_recall | 1.0000 | 42/1 | True |
| absence | cortex[disable_supersession] | answer_support_recall | 0.0000 | 42/48 | False |
| absence | cortex[disable_supersession] | contradiction_exposure_rate | 0.0000 | 42/48 | False |
| absence | cortex[disable_supersession] | current_state_accuracy | 1.0000 | 42/1 | True |
| absence | cortex[disable_supersession] | deletion_compliance | 1.0000 | 42/1 | True |
| absence | cortex[disable_supersession] | evidence_resolution_rate | 1.0000 | 42/1 | True |
| absence | cortex[disable_supersession] | extraction_recall | 1.0000 | 42/1 | True |
| absence | cortex[disable_supersession] | extraction_spurious_rate | 1.0000 | 42/1 | True |
| absence | cortex[disable_supersession] | false_certainty_rate | 0.0000 | 42/48 | False |
| absence | cortex[disable_supersession] | lineage_completeness | 1.0000 | 42/1 | True |
| absence | cortex[disable_supersession] | mrr | 0.0000 | 42/48 | False |
| absence | cortex[disable_supersession] | ndcg_at_k | 0.0000 | 42/48 | False |
| absence | cortex[disable_supersession] | precision_at_k | 0.0000 | 42/48 | False |
| absence | cortex[disable_supersession] | provenance_coverage | 1.0000 | 42/1 | True |
| absence | cortex[disable_supersession] | recall_at_k | 0.0000 | 42/48 | False |
| absence | cortex[disable_supersession] | scope_accuracy | 1.0000 | 42/1 | True |
| absence | cortex[disable_supersession] | set_f1 | 1.0000 | 42/1 | True |
| absence | cortex[disable_supersession] | stale_leak_rate | 0.0000 | 42/48 | False |
| absence | cortex[disable_supersession] | supersession_accuracy | 1.0000 | 42/1 | True |
| absence | cortex[disable_supersession] | unsupported_claim_rate | 0.0000 | 42/48 | False |
| absence | raw_context | abstention_recall | 0.0000 | 42/48 | False |
| absence | raw_context | answer_support_recall | 0.0000 | 42/48 | False |
| absence | raw_context | contradiction_exposure_rate | 0.0000 | 42/48 | False |
| absence | raw_context | current_state_accuracy | 1.0000 | 42/1 | True |
| absence | raw_context | deletion_compliance | 1.0000 | 42/1 | True |
| absence | raw_context | evidence_resolution_rate | 1.0000 | 42/1 | True |
| absence | raw_context | false_certainty_rate | 0.0000 | 42/48 | False |
| absence | raw_context | lineage_completeness | 1.0000 | 42/1 | True |
| absence | raw_context | mrr | 0.0000 | 42/48 | False |
| absence | raw_context | ndcg_at_k | 0.0000 | 42/48 | False |
| absence | raw_context | precision_at_k | 0.0000 | 42/48 | False |
| absence | raw_context | provenance_coverage | 1.0000 | 42/1 | True |
| absence | raw_context | recall_at_k | 0.0000 | 42/48 | False |
| absence | raw_context | scope_accuracy | 0.0000 | 42/48 | False |
| absence | raw_context | set_f1 | 0.0000 | 42/48 | False |
| absence | raw_context | stale_leak_rate | 0.0000 | 42/48 | False |
| absence | raw_context | supersession_accuracy | 1.0000 | 42/1 | True |
| absence | raw_context | unsupported_claim_rate | 0.0000 | 42/48 | False |
| aggregation | bm25 | abstention_recall | 1.0000 | 41/1 | True |
| aggregation | bm25 | answer_support_recall | 1.0000 | 41/1 | True |
| aggregation | bm25 | contradiction_exposure_rate | 0.0000 | 41/48 | False |
| aggregation | bm25 | current_state_accuracy | 1.0000 | 41/1 | True |
| aggregation | bm25 | deletion_compliance | 1.0000 | 41/1 | True |
| aggregation | bm25 | evidence_resolution_rate | 1.0000 | 41/1 | True |
| aggregation | bm25 | false_certainty_rate | 0.0000 | 41/48 | False |
| aggregation | bm25 | lineage_completeness | 1.0000 | 41/1 | True |
| aggregation | bm25 | mrr | 1.0000 | 41/1 | True |
| aggregation | bm25 | ndcg_at_k | 1.0000 | 41/1 | True |
| aggregation | bm25 | precision_at_k | 1.0000 | 41/1 | True |
| aggregation | bm25 | provenance_coverage | 1.0000 | 41/1 | True |
| aggregation | bm25 | recall_at_k | 1.0000 | 41/1 | True |
| aggregation | bm25 | scope_accuracy | 1.0000 | 41/1 | True |
| aggregation | bm25 | set_f1 | 1.0000 | 41/1 | True |
| aggregation | bm25 | stale_leak_rate | 0.0000 | 41/48 | False |
| aggregation | bm25 | supersession_accuracy | 1.0000 | 41/1 | True |
| aggregation | bm25 | unsupported_claim_rate | 0.0000 | 41/48 | False |
| aggregation | cortex | abstention_recall | 1.0000 | 41/1 | True |
| aggregation | cortex | answer_support_recall | 1.0000 | 41/1 | True |
| aggregation | cortex | contradiction_exposure_rate | 0.0000 | 41/48 | False |
| aggregation | cortex | current_state_accuracy | 1.0000 | 41/1 | True |
| aggregation | cortex | deletion_compliance | 1.0000 | 41/1 | True |
| aggregation | cortex | evidence_resolution_rate | 1.0000 | 41/1 | True |
| aggregation | cortex | extraction_recall | 1.0000 | 41/1 | True |
| aggregation | cortex | extraction_spurious_rate | 0.0000 | 41/48 | False |
| aggregation | cortex | false_certainty_rate | 0.0000 | 41/48 | False |
| aggregation | cortex | lineage_completeness | 1.0000 | 41/1 | True |
| aggregation | cortex | mrr | 1.0000 | 41/1 | True |
| aggregation | cortex | ndcg_at_k | 1.0000 | 41/1 | True |
| aggregation | cortex | precision_at_k | 1.0000 | 41/1 | True |
| aggregation | cortex | provenance_coverage | 1.0000 | 41/1 | True |
| aggregation | cortex | recall_at_k | 1.0000 | 41/1 | True |
| aggregation | cortex | scope_accuracy | 1.0000 | 41/1 | True |
| aggregation | cortex | set_f1 | 1.0000 | 41/1 | True |
| aggregation | cortex | stale_leak_rate | 0.0000 | 41/48 | False |
| aggregation | cortex | supersession_accuracy | 1.0000 | 41/1 | True |
| aggregation | cortex | unsupported_claim_rate | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_authority] | abstention_recall | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_authority] | answer_support_recall | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_authority] | contradiction_exposure_rate | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_authority] | current_state_accuracy | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_authority] | deletion_compliance | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_authority] | evidence_resolution_rate | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_authority] | extraction_recall | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_authority] | extraction_spurious_rate | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_authority] | false_certainty_rate | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_authority] | lineage_completeness | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_authority] | mrr | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_authority] | ndcg_at_k | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_authority] | precision_at_k | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_authority] | provenance_coverage | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_authority] | recall_at_k | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_authority] | scope_accuracy | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_authority] | set_f1 | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_authority] | stale_leak_rate | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_authority] | supersession_accuracy | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_authority] | unsupported_claim_rate | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_contradiction_penalty] | abstention_recall | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_contradiction_penalty] | answer_support_recall | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_contradiction_penalty] | contradiction_exposure_rate | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_contradiction_penalty] | current_state_accuracy | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_contradiction_penalty] | deletion_compliance | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_contradiction_penalty] | evidence_resolution_rate | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_contradiction_penalty] | extraction_recall | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_contradiction_penalty] | extraction_spurious_rate | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_contradiction_penalty] | false_certainty_rate | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_contradiction_penalty] | lineage_completeness | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_contradiction_penalty] | mrr | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_contradiction_penalty] | ndcg_at_k | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_contradiction_penalty] | precision_at_k | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_contradiction_penalty] | provenance_coverage | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_contradiction_penalty] | recall_at_k | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_contradiction_penalty] | scope_accuracy | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_contradiction_penalty] | set_f1 | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_contradiction_penalty] | stale_leak_rate | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_contradiction_penalty] | supersession_accuracy | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_contradiction_penalty] | unsupported_claim_rate | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_dense] | abstention_recall | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_dense] | answer_support_recall | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_dense] | contradiction_exposure_rate | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_dense] | current_state_accuracy | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_dense] | deletion_compliance | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_dense] | evidence_resolution_rate | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_dense] | extraction_recall | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_dense] | extraction_spurious_rate | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_dense] | false_certainty_rate | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_dense] | lineage_completeness | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_dense] | mrr | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_dense] | ndcg_at_k | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_dense] | precision_at_k | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_dense] | provenance_coverage | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_dense] | recall_at_k | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_dense] | scope_accuracy | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_dense] | set_f1 | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_dense] | stale_leak_rate | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_dense] | supersession_accuracy | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_dense] | unsupported_claim_rate | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_evidence_ledger] | abstention_recall | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_evidence_ledger] | answer_support_recall | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_evidence_ledger] | contradiction_exposure_rate | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_evidence_ledger] | current_state_accuracy | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_evidence_ledger] | deletion_compliance | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_evidence_ledger] | evidence_resolution_rate | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_evidence_ledger] | extraction_recall | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_evidence_ledger] | extraction_spurious_rate | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_evidence_ledger] | false_certainty_rate | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_evidence_ledger] | lineage_completeness | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_evidence_ledger] | mrr | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_evidence_ledger] | ndcg_at_k | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_evidence_ledger] | precision_at_k | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_evidence_ledger] | provenance_coverage | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_evidence_ledger] | recall_at_k | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_evidence_ledger] | scope_accuracy | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_evidence_ledger] | set_f1 | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_evidence_ledger] | stale_leak_rate | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_evidence_ledger] | supersession_accuracy | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_evidence_ledger] | unsupported_claim_rate | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_graph_density] | abstention_recall | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_graph_density] | answer_support_recall | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_graph_density] | contradiction_exposure_rate | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_graph_density] | current_state_accuracy | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_graph_density] | deletion_compliance | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_graph_density] | evidence_resolution_rate | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_graph_density] | extraction_recall | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_graph_density] | extraction_spurious_rate | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_graph_density] | false_certainty_rate | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_graph_density] | lineage_completeness | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_graph_density] | mrr | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_graph_density] | ndcg_at_k | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_graph_density] | precision_at_k | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_graph_density] | provenance_coverage | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_graph_density] | recall_at_k | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_graph_density] | scope_accuracy | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_graph_density] | set_f1 | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_graph_density] | stale_leak_rate | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_graph_density] | supersession_accuracy | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_graph_density] | unsupported_claim_rate | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_supersession] | abstention_recall | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_supersession] | answer_support_recall | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_supersession] | contradiction_exposure_rate | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_supersession] | current_state_accuracy | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_supersession] | deletion_compliance | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_supersession] | evidence_resolution_rate | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_supersession] | extraction_recall | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_supersession] | extraction_spurious_rate | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_supersession] | false_certainty_rate | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_supersession] | lineage_completeness | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_supersession] | mrr | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_supersession] | ndcg_at_k | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_supersession] | precision_at_k | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_supersession] | provenance_coverage | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_supersession] | recall_at_k | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_supersession] | scope_accuracy | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_supersession] | set_f1 | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_supersession] | stale_leak_rate | 0.0000 | 41/48 | False |
| aggregation | cortex[disable_supersession] | supersession_accuracy | 1.0000 | 41/1 | True |
| aggregation | cortex[disable_supersession] | unsupported_claim_rate | 0.0000 | 41/48 | False |
| aggregation | raw_context | abstention_recall | 1.0000 | 41/1 | True |
| aggregation | raw_context | answer_support_recall | 1.0000 | 41/1 | True |
| aggregation | raw_context | contradiction_exposure_rate | 0.0000 | 41/48 | False |
| aggregation | raw_context | current_state_accuracy | 1.0000 | 41/1 | True |
| aggregation | raw_context | deletion_compliance | 1.0000 | 41/1 | True |
| aggregation | raw_context | evidence_resolution_rate | 1.0000 | 41/1 | True |
| aggregation | raw_context | false_certainty_rate | 0.0000 | 41/48 | False |
| aggregation | raw_context | lineage_completeness | 1.0000 | 41/1 | True |
| aggregation | raw_context | mrr | 1.0000 | 41/1 | True |
| aggregation | raw_context | ndcg_at_k | 1.0000 | 41/1 | True |
| aggregation | raw_context | precision_at_k | 0.7561 | 41/97 | False |
| aggregation | raw_context | provenance_coverage | 1.0000 | 41/1 | True |
| aggregation | raw_context | recall_at_k | 1.0000 | 41/1 | True |
| aggregation | raw_context | scope_accuracy | 0.0244 | 41/62 | False |
| aggregation | raw_context | set_f1 | 0.8606 | 41/45 | False |
| aggregation | raw_context | stale_leak_rate | 0.0000 | 41/48 | False |
| aggregation | raw_context | supersession_accuracy | 1.0000 | 41/1 | True |
| aggregation | raw_context | unsupported_claim_rate | 0.0000 | 41/48 | False |
| cascade | bm25 | abstention_recall | 1.0000 | 41/1 | True |
| cascade | bm25 | answer_support_recall | 1.0000 | 41/1 | True |
| cascade | bm25 | cascade_correctness_hop1 | 0.0000 | 41/48 | False |
| cascade | bm25 | cascade_correctness_hop2 | 0.0000 | 41/48 | False |
| cascade | bm25 | contradiction_exposure_rate | 0.0000 | 41/48 | False |
| cascade | bm25 | current_state_accuracy | 1.0000 | 41/1 | True |
| cascade | bm25 | deletion_compliance | 0.0000 | 41/48 | False |
| cascade | bm25 | evidence_resolution_rate | 1.0000 | 41/1 | True |
| cascade | bm25 | false_certainty_rate | 0.0000 | 41/48 | False |
| cascade | bm25 | lineage_completeness | 1.0000 | 41/1 | True |
| cascade | bm25 | mrr | 0.5976 | 41/153 | False |
| cascade | bm25 | ndcg_at_k | 0.7029 | 41/120 | False |
| cascade | bm25 | precision_at_k | 0.3333 | 41/168 | False |
| cascade | bm25 | provenance_coverage | 1.0000 | 41/1 | True |
| cascade | bm25 | recall_at_k | 1.0000 | 41/1 | True |
| cascade | bm25 | scope_accuracy | 0.0000 | 41/48 | False |
| cascade | bm25 | set_f1 | 0.5000 | 41/170 | False |
| cascade | bm25 | stale_leak_rate | 1.0000 | 41/1 | True |
| cascade | bm25 | supersession_accuracy | 0.0000 | 41/48 | False |
| cascade | bm25 | unsupported_claim_rate | 0.0000 | 41/48 | False |
| cascade | cortex | abstention_recall | 1.0000 | 41/1 | True |
| cascade | cortex | answer_support_recall | 1.0000 | 41/1 | True |
| cascade | cortex | cascade_correctness_hop1 | 1.0000 | 41/1 | True |
| cascade | cortex | cascade_correctness_hop2 | 1.0000 | 41/1 | True |
| cascade | cortex | contradiction_exposure_rate | 0.0000 | 41/48 | False |
| cascade | cortex | current_state_accuracy | 1.0000 | 41/1 | True |
| cascade | cortex | deletion_compliance | 1.0000 | 41/1 | True |
| cascade | cortex | evidence_resolution_rate | 1.0000 | 41/1 | True |
| cascade | cortex | extraction_recall | 1.0000 | 41/1 | True |
| cascade | cortex | extraction_spurious_rate | 0.3333 | 41/168 | False |
| cascade | cortex | false_certainty_rate | 0.0000 | 41/48 | False |
| cascade | cortex | lineage_completeness | 1.0000 | 41/1 | True |
| cascade | cortex | mrr | 0.5976 | 41/153 | False |
| cascade | cortex | ndcg_at_k | 0.7029 | 41/120 | False |
| cascade | cortex | precision_at_k | 0.5000 | 41/170 | False |
| cascade | cortex | provenance_coverage | 1.0000 | 41/1 | True |
| cascade | cortex | recall_at_k | 1.0000 | 41/1 | True |
| cascade | cortex | scope_accuracy | 0.0000 | 41/48 | False |
| cascade | cortex | set_f1 | 0.6667 | 41/133 | False |
| cascade | cortex | stale_leak_rate | 0.0000 | 41/48 | False |
| cascade | cortex | supersession_accuracy | 1.0000 | 41/1 | True |
| cascade | cortex | unsupported_claim_rate | 0.0000 | 41/48 | False |
| cascade | cortex[disable_authority] | abstention_recall | 1.0000 | 41/1 | True |
| cascade | cortex[disable_authority] | answer_support_recall | 1.0000 | 41/1 | True |
| cascade | cortex[disable_authority] | cascade_correctness_hop1 | 1.0000 | 41/1 | True |
| cascade | cortex[disable_authority] | cascade_correctness_hop2 | 1.0000 | 41/1 | True |
| cascade | cortex[disable_authority] | contradiction_exposure_rate | 0.0000 | 41/48 | False |
| cascade | cortex[disable_authority] | current_state_accuracy | 1.0000 | 41/1 | True |
| cascade | cortex[disable_authority] | deletion_compliance | 1.0000 | 41/1 | True |
| cascade | cortex[disable_authority] | evidence_resolution_rate | 1.0000 | 41/1 | True |
| cascade | cortex[disable_authority] | extraction_recall | 1.0000 | 41/1 | True |
| cascade | cortex[disable_authority] | extraction_spurious_rate | 0.3333 | 41/168 | False |
| cascade | cortex[disable_authority] | false_certainty_rate | 0.0000 | 41/48 | False |
| cascade | cortex[disable_authority] | lineage_completeness | 1.0000 | 41/1 | True |
| cascade | cortex[disable_authority] | mrr | 0.5976 | 41/153 | False |
| cascade | cortex[disable_authority] | ndcg_at_k | 0.7029 | 41/120 | False |
| cascade | cortex[disable_authority] | precision_at_k | 0.5000 | 41/170 | False |
| cascade | cortex[disable_authority] | provenance_coverage | 1.0000 | 41/1 | True |
| cascade | cortex[disable_authority] | recall_at_k | 1.0000 | 41/1 | True |
| cascade | cortex[disable_authority] | scope_accuracy | 0.0000 | 41/48 | False |
| cascade | cortex[disable_authority] | set_f1 | 0.6667 | 41/133 | False |
| cascade | cortex[disable_authority] | stale_leak_rate | 0.0000 | 41/48 | False |
| cascade | cortex[disable_authority] | supersession_accuracy | 1.0000 | 41/1 | True |
| cascade | cortex[disable_authority] | unsupported_claim_rate | 0.0000 | 41/48 | False |
| cascade | cortex[disable_contradiction_penalty] | abstention_recall | 1.0000 | 41/1 | True |
| cascade | cortex[disable_contradiction_penalty] | answer_support_recall | 1.0000 | 41/1 | True |
| cascade | cortex[disable_contradiction_penalty] | cascade_correctness_hop1 | 1.0000 | 41/1 | True |
| cascade | cortex[disable_contradiction_penalty] | cascade_correctness_hop2 | 1.0000 | 41/1 | True |
| cascade | cortex[disable_contradiction_penalty] | contradiction_exposure_rate | 0.0000 | 41/48 | False |
| cascade | cortex[disable_contradiction_penalty] | current_state_accuracy | 1.0000 | 41/1 | True |
| cascade | cortex[disable_contradiction_penalty] | deletion_compliance | 1.0000 | 41/1 | True |
| cascade | cortex[disable_contradiction_penalty] | evidence_resolution_rate | 1.0000 | 41/1 | True |
| cascade | cortex[disable_contradiction_penalty] | extraction_recall | 1.0000 | 41/1 | True |
| cascade | cortex[disable_contradiction_penalty] | extraction_spurious_rate | 0.3333 | 41/168 | False |
| cascade | cortex[disable_contradiction_penalty] | false_certainty_rate | 0.0000 | 41/48 | False |
| cascade | cortex[disable_contradiction_penalty] | lineage_completeness | 1.0000 | 41/1 | True |
| cascade | cortex[disable_contradiction_penalty] | mrr | 0.5976 | 41/153 | False |
| cascade | cortex[disable_contradiction_penalty] | ndcg_at_k | 0.7029 | 41/120 | False |
| cascade | cortex[disable_contradiction_penalty] | precision_at_k | 0.5000 | 41/170 | False |
| cascade | cortex[disable_contradiction_penalty] | provenance_coverage | 1.0000 | 41/1 | True |
| cascade | cortex[disable_contradiction_penalty] | recall_at_k | 1.0000 | 41/1 | True |
| cascade | cortex[disable_contradiction_penalty] | scope_accuracy | 0.0000 | 41/48 | False |
| cascade | cortex[disable_contradiction_penalty] | set_f1 | 0.6667 | 41/133 | False |
| cascade | cortex[disable_contradiction_penalty] | stale_leak_rate | 0.0000 | 41/48 | False |
| cascade | cortex[disable_contradiction_penalty] | supersession_accuracy | 1.0000 | 41/1 | True |
| cascade | cortex[disable_contradiction_penalty] | unsupported_claim_rate | 0.0000 | 41/48 | False |
| cascade | cortex[disable_dense] | abstention_recall | 1.0000 | 41/1 | True |
| cascade | cortex[disable_dense] | answer_support_recall | 1.0000 | 41/1 | True |
| cascade | cortex[disable_dense] | cascade_correctness_hop1 | 1.0000 | 41/1 | True |
| cascade | cortex[disable_dense] | cascade_correctness_hop2 | 1.0000 | 41/1 | True |
| cascade | cortex[disable_dense] | contradiction_exposure_rate | 0.0000 | 41/48 | False |
| cascade | cortex[disable_dense] | current_state_accuracy | 1.0000 | 41/1 | True |
| cascade | cortex[disable_dense] | deletion_compliance | 1.0000 | 41/1 | True |
| cascade | cortex[disable_dense] | evidence_resolution_rate | 1.0000 | 41/1 | True |
| cascade | cortex[disable_dense] | extraction_recall | 1.0000 | 41/1 | True |
| cascade | cortex[disable_dense] | extraction_spurious_rate | 0.3333 | 41/168 | False |
| cascade | cortex[disable_dense] | false_certainty_rate | 0.0000 | 41/48 | False |
| cascade | cortex[disable_dense] | lineage_completeness | 1.0000 | 41/1 | True |
| cascade | cortex[disable_dense] | mrr | 0.5976 | 41/153 | False |
| cascade | cortex[disable_dense] | ndcg_at_k | 0.7029 | 41/120 | False |
| cascade | cortex[disable_dense] | precision_at_k | 0.5000 | 41/170 | False |
| cascade | cortex[disable_dense] | provenance_coverage | 1.0000 | 41/1 | True |
| cascade | cortex[disable_dense] | recall_at_k | 1.0000 | 41/1 | True |
| cascade | cortex[disable_dense] | scope_accuracy | 0.0000 | 41/48 | False |
| cascade | cortex[disable_dense] | set_f1 | 0.6667 | 41/133 | False |
| cascade | cortex[disable_dense] | stale_leak_rate | 0.0000 | 41/48 | False |
| cascade | cortex[disable_dense] | supersession_accuracy | 1.0000 | 41/1 | True |
| cascade | cortex[disable_dense] | unsupported_claim_rate | 0.0000 | 41/48 | False |
| cascade | cortex[disable_evidence_ledger] | abstention_recall | 1.0000 | 41/1 | True |
| cascade | cortex[disable_evidence_ledger] | answer_support_recall | 0.0000 | 41/48 | False |
| cascade | cortex[disable_evidence_ledger] | cascade_correctness_hop1 | 1.0000 | 41/1 | True |
| cascade | cortex[disable_evidence_ledger] | cascade_correctness_hop2 | 1.0000 | 41/1 | True |
| cascade | cortex[disable_evidence_ledger] | contradiction_exposure_rate | 0.0000 | 41/48 | False |
| cascade | cortex[disable_evidence_ledger] | current_state_accuracy | 1.0000 | 41/1 | True |
| cascade | cortex[disable_evidence_ledger] | deletion_compliance | 1.0000 | 41/1 | True |
| cascade | cortex[disable_evidence_ledger] | evidence_resolution_rate | 0.0000 | 41/48 | False |
| cascade | cortex[disable_evidence_ledger] | extraction_recall | 1.0000 | 41/1 | True |
| cascade | cortex[disable_evidence_ledger] | extraction_spurious_rate | 0.3333 | 41/168 | False |
| cascade | cortex[disable_evidence_ledger] | false_certainty_rate | 1.0000 | 41/1 | True |
| cascade | cortex[disable_evidence_ledger] | lineage_completeness | 1.0000 | 41/1 | True |
| cascade | cortex[disable_evidence_ledger] | mrr | 0.5976 | 41/153 | False |
| cascade | cortex[disable_evidence_ledger] | ndcg_at_k | 0.7029 | 41/120 | False |
| cascade | cortex[disable_evidence_ledger] | precision_at_k | 0.5000 | 41/170 | False |
| cascade | cortex[disable_evidence_ledger] | provenance_coverage | 0.0000 | 41/48 | False |
| cascade | cortex[disable_evidence_ledger] | recall_at_k | 1.0000 | 41/1 | True |
| cascade | cortex[disable_evidence_ledger] | scope_accuracy | 0.0000 | 41/48 | False |
| cascade | cortex[disable_evidence_ledger] | set_f1 | 0.6667 | 41/133 | False |
| cascade | cortex[disable_evidence_ledger] | stale_leak_rate | 0.0000 | 41/48 | False |
| cascade | cortex[disable_evidence_ledger] | supersession_accuracy | 1.0000 | 41/1 | True |
| cascade | cortex[disable_evidence_ledger] | unsupported_claim_rate | 0.0000 | 41/48 | False |
| cascade | cortex[disable_graph_density] | abstention_recall | 1.0000 | 41/1 | True |
| cascade | cortex[disable_graph_density] | answer_support_recall | 1.0000 | 41/1 | True |
| cascade | cortex[disable_graph_density] | cascade_correctness_hop1 | 1.0000 | 41/1 | True |
| cascade | cortex[disable_graph_density] | cascade_correctness_hop2 | 1.0000 | 41/1 | True |
| cascade | cortex[disable_graph_density] | contradiction_exposure_rate | 0.0000 | 41/48 | False |
| cascade | cortex[disable_graph_density] | current_state_accuracy | 1.0000 | 41/1 | True |
| cascade | cortex[disable_graph_density] | deletion_compliance | 1.0000 | 41/1 | True |
| cascade | cortex[disable_graph_density] | evidence_resolution_rate | 1.0000 | 41/1 | True |
| cascade | cortex[disable_graph_density] | extraction_recall | 1.0000 | 41/1 | True |
| cascade | cortex[disable_graph_density] | extraction_spurious_rate | 0.3333 | 41/168 | False |
| cascade | cortex[disable_graph_density] | false_certainty_rate | 0.0000 | 41/48 | False |
| cascade | cortex[disable_graph_density] | lineage_completeness | 1.0000 | 41/1 | True |
| cascade | cortex[disable_graph_density] | mrr | 0.5976 | 41/153 | False |
| cascade | cortex[disable_graph_density] | ndcg_at_k | 0.7029 | 41/120 | False |
| cascade | cortex[disable_graph_density] | precision_at_k | 0.5000 | 41/170 | False |
| cascade | cortex[disable_graph_density] | provenance_coverage | 1.0000 | 41/1 | True |
| cascade | cortex[disable_graph_density] | recall_at_k | 1.0000 | 41/1 | True |
| cascade | cortex[disable_graph_density] | scope_accuracy | 0.0000 | 41/48 | False |
| cascade | cortex[disable_graph_density] | set_f1 | 0.6667 | 41/133 | False |
| cascade | cortex[disable_graph_density] | stale_leak_rate | 0.0000 | 41/48 | False |
| cascade | cortex[disable_graph_density] | supersession_accuracy | 1.0000 | 41/1 | True |
| cascade | cortex[disable_graph_density] | unsupported_claim_rate | 0.0000 | 41/48 | False |
| cascade | cortex[disable_supersession] | abstention_recall | 1.0000 | 41/1 | True |
| cascade | cortex[disable_supersession] | answer_support_recall | 1.0000 | 41/1 | True |
| cascade | cortex[disable_supersession] | cascade_correctness_hop1 | 0.0000 | 41/48 | False |
| cascade | cortex[disable_supersession] | cascade_correctness_hop2 | 0.0000 | 41/48 | False |
| cascade | cortex[disable_supersession] | contradiction_exposure_rate | 0.0000 | 41/48 | False |
| cascade | cortex[disable_supersession] | current_state_accuracy | 1.0000 | 41/1 | True |
| cascade | cortex[disable_supersession] | deletion_compliance | 0.0000 | 41/48 | False |
| cascade | cortex[disable_supersession] | evidence_resolution_rate | 1.0000 | 41/1 | True |
| cascade | cortex[disable_supersession] | extraction_recall | 1.0000 | 41/1 | True |
| cascade | cortex[disable_supersession] | extraction_spurious_rate | 0.3333 | 41/168 | False |
| cascade | cortex[disable_supersession] | false_certainty_rate | 0.0000 | 41/48 | False |
| cascade | cortex[disable_supersession] | lineage_completeness | 0.0000 | 41/48 | False |
| cascade | cortex[disable_supersession] | mrr | 0.5813 | 41/157 | False |
| cascade | cortex[disable_supersession] | ndcg_at_k | 0.6902 | 41/125 | False |
| cascade | cortex[disable_supersession] | precision_at_k | 0.3333 | 41/168 | False |
| cascade | cortex[disable_supersession] | provenance_coverage | 1.0000 | 41/1 | True |
| cascade | cortex[disable_supersession] | recall_at_k | 1.0000 | 41/1 | True |
| cascade | cortex[disable_supersession] | scope_accuracy | 0.0000 | 41/48 | False |
| cascade | cortex[disable_supersession] | set_f1 | 0.5000 | 41/170 | False |
| cascade | cortex[disable_supersession] | stale_leak_rate | 1.0000 | 41/1 | True |
| cascade | cortex[disable_supersession] | supersession_accuracy | 0.0000 | 41/48 | False |
| cascade | cortex[disable_supersession] | unsupported_claim_rate | 0.0000 | 41/48 | False |
| cascade | raw_context | abstention_recall | 1.0000 | 41/1 | True |
| cascade | raw_context | answer_support_recall | 1.0000 | 41/1 | True |
| cascade | raw_context | cascade_correctness_hop1 | 0.0000 | 41/48 | False |
| cascade | raw_context | cascade_correctness_hop2 | 0.0000 | 41/48 | False |
| cascade | raw_context | contradiction_exposure_rate | 0.0000 | 41/48 | False |
| cascade | raw_context | current_state_accuracy | 1.0000 | 41/1 | True |
| cascade | raw_context | deletion_compliance | 0.0000 | 41/48 | False |
| cascade | raw_context | evidence_resolution_rate | 1.0000 | 41/1 | True |
| cascade | raw_context | false_certainty_rate | 0.0000 | 41/48 | False |
| cascade | raw_context | lineage_completeness | 1.0000 | 41/1 | True |
| cascade | raw_context | mrr | 0.5000 | 41/170 | False |
| cascade | raw_context | ndcg_at_k | 0.6309 | 41/144 | False |
| cascade | raw_context | precision_at_k | 0.2520 | 41/153 | False |
| cascade | raw_context | provenance_coverage | 1.0000 | 41/1 | True |
| cascade | raw_context | recall_at_k | 1.0000 | 41/1 | True |
| cascade | raw_context | scope_accuracy | 0.0000 | 41/48 | False |
| cascade | raw_context | set_f1 | 0.4024 | 41/173 | False |
| cascade | raw_context | stale_leak_rate | 1.0000 | 41/1 | True |
| cascade | raw_context | supersession_accuracy | 0.0000 | 41/48 | False |
| cascade | raw_context | unsupported_claim_rate | 0.0000 | 41/48 | False |
| deletion | bm25 | abstention_recall | 1.0000 | 41/1 | True |
| deletion | bm25 | answer_support_recall | 1.0000 | 41/1 | True |
| deletion | bm25 | contradiction_exposure_rate | 0.0000 | 41/48 | False |
| deletion | bm25 | current_state_accuracy | 1.0000 | 41/1 | True |
| deletion | bm25 | deletion_compliance | 0.0000 | 41/48 | False |
| deletion | bm25 | evidence_resolution_rate | 1.0000 | 41/1 | True |
| deletion | bm25 | false_certainty_rate | 0.0000 | 41/48 | False |
| deletion | bm25 | lineage_completeness | 1.0000 | 41/1 | True |
| deletion | bm25 | mrr | 0.5976 | 41/153 | False |
| deletion | bm25 | ndcg_at_k | 0.7029 | 41/120 | False |
| deletion | bm25 | precision_at_k | 0.3333 | 41/168 | False |
| deletion | bm25 | provenance_coverage | 1.0000 | 41/1 | True |
| deletion | bm25 | recall_at_k | 1.0000 | 41/1 | True |
| deletion | bm25 | scope_accuracy | 0.0000 | 41/48 | False |
| deletion | bm25 | set_f1 | 0.5000 | 41/170 | False |
| deletion | bm25 | stale_leak_rate | 1.0000 | 41/1 | True |
| deletion | bm25 | supersession_accuracy | 0.0000 | 41/48 | False |
| deletion | bm25 | unsupported_claim_rate | 0.0000 | 41/48 | False |
| deletion | cortex | abstention_recall | 1.0000 | 41/1 | True |
| deletion | cortex | answer_support_recall | 0.9756 | 41/9 | True |
| deletion | cortex | contradiction_exposure_rate | 0.0000 | 41/48 | False |
| deletion | cortex | current_state_accuracy | 0.9756 | 41/9 | True |
| deletion | cortex | deletion_compliance | 1.0000 | 41/1 | True |
| deletion | cortex | evidence_resolution_rate | 1.0000 | 41/1 | True |
| deletion | cortex | extraction_recall | 1.0000 | 41/1 | True |
| deletion | cortex | extraction_spurious_rate | 0.6667 | 41/133 | False |
| deletion | cortex | false_certainty_rate | 0.0000 | 41/48 | False |
| deletion | cortex | lineage_completeness | 1.0000 | 41/1 | True |
| deletion | cortex | mrr | 0.5854 | 41/156 | False |
| deletion | cortex | ndcg_at_k | 0.6876 | 41/126 | False |
| deletion | cortex | precision_at_k | 0.4878 | 41/171 | False |
| deletion | cortex | provenance_coverage | 0.9756 | 41/9 | True |
| deletion | cortex | recall_at_k | 0.9756 | 41/9 | True |
| deletion | cortex | scope_accuracy | 0.0000 | 41/48 | False |
| deletion | cortex | set_f1 | 0.6504 | 41/138 | False |
| deletion | cortex | stale_leak_rate | 0.0000 | 41/48 | False |
| deletion | cortex | supersession_accuracy | 1.0000 | 41/1 | True |
| deletion | cortex | unsupported_claim_rate | 0.0000 | 41/48 | False |
| deletion | cortex[disable_authority] | abstention_recall | 1.0000 | 41/1 | True |
| deletion | cortex[disable_authority] | answer_support_recall | 0.9756 | 41/9 | True |
| deletion | cortex[disable_authority] | contradiction_exposure_rate | 0.0000 | 41/48 | False |
| deletion | cortex[disable_authority] | current_state_accuracy | 0.9756 | 41/9 | True |
| deletion | cortex[disable_authority] | deletion_compliance | 1.0000 | 41/1 | True |
| deletion | cortex[disable_authority] | evidence_resolution_rate | 1.0000 | 41/1 | True |
| deletion | cortex[disable_authority] | extraction_recall | 1.0000 | 41/1 | True |
| deletion | cortex[disable_authority] | extraction_spurious_rate | 0.6667 | 41/133 | False |
| deletion | cortex[disable_authority] | false_certainty_rate | 0.0000 | 41/48 | False |
| deletion | cortex[disable_authority] | lineage_completeness | 1.0000 | 41/1 | True |
| deletion | cortex[disable_authority] | mrr | 0.5854 | 41/156 | False |
| deletion | cortex[disable_authority] | ndcg_at_k | 0.6876 | 41/126 | False |
| deletion | cortex[disable_authority] | precision_at_k | 0.4878 | 41/171 | False |
| deletion | cortex[disable_authority] | provenance_coverage | 0.9756 | 41/9 | True |
| deletion | cortex[disable_authority] | recall_at_k | 0.9756 | 41/9 | True |
| deletion | cortex[disable_authority] | scope_accuracy | 0.0000 | 41/48 | False |
| deletion | cortex[disable_authority] | set_f1 | 0.6504 | 41/138 | False |
| deletion | cortex[disable_authority] | stale_leak_rate | 0.0000 | 41/48 | False |
| deletion | cortex[disable_authority] | supersession_accuracy | 1.0000 | 41/1 | True |
| deletion | cortex[disable_authority] | unsupported_claim_rate | 0.0000 | 41/48 | False |
| deletion | cortex[disable_contradiction_penalty] | abstention_recall | 1.0000 | 41/1 | True |
| deletion | cortex[disable_contradiction_penalty] | answer_support_recall | 1.0000 | 41/1 | True |
| deletion | cortex[disable_contradiction_penalty] | contradiction_exposure_rate | 0.0000 | 41/48 | False |
| deletion | cortex[disable_contradiction_penalty] | current_state_accuracy | 1.0000 | 41/1 | True |
| deletion | cortex[disable_contradiction_penalty] | deletion_compliance | 1.0000 | 41/1 | True |
| deletion | cortex[disable_contradiction_penalty] | evidence_resolution_rate | 1.0000 | 41/1 | True |
| deletion | cortex[disable_contradiction_penalty] | extraction_recall | 1.0000 | 41/1 | True |
| deletion | cortex[disable_contradiction_penalty] | extraction_spurious_rate | 0.6667 | 41/133 | False |
| deletion | cortex[disable_contradiction_penalty] | false_certainty_rate | 0.0000 | 41/48 | False |
| deletion | cortex[disable_contradiction_penalty] | lineage_completeness | 1.0000 | 41/1 | True |
| deletion | cortex[disable_contradiction_penalty] | mrr | 0.6098 | 41/150 | False |
| deletion | cortex[disable_contradiction_penalty] | ndcg_at_k | 0.7119 | 41/116 | False |
| deletion | cortex[disable_contradiction_penalty] | precision_at_k | 0.5000 | 41/170 | False |
| deletion | cortex[disable_contradiction_penalty] | provenance_coverage | 1.0000 | 41/1 | True |
| deletion | cortex[disable_contradiction_penalty] | recall_at_k | 1.0000 | 41/1 | True |
| deletion | cortex[disable_contradiction_penalty] | scope_accuracy | 0.0000 | 41/48 | False |
| deletion | cortex[disable_contradiction_penalty] | set_f1 | 0.6667 | 41/133 | False |
| deletion | cortex[disable_contradiction_penalty] | stale_leak_rate | 0.0000 | 41/48 | False |
| deletion | cortex[disable_contradiction_penalty] | supersession_accuracy | 1.0000 | 41/1 | True |
| deletion | cortex[disable_contradiction_penalty] | unsupported_claim_rate | 0.0000 | 41/48 | False |
| deletion | cortex[disable_dense] | abstention_recall | 1.0000 | 41/1 | True |
| deletion | cortex[disable_dense] | answer_support_recall | 0.9756 | 41/9 | True |
| deletion | cortex[disable_dense] | contradiction_exposure_rate | 0.0000 | 41/48 | False |
| deletion | cortex[disable_dense] | current_state_accuracy | 0.9756 | 41/9 | True |
| deletion | cortex[disable_dense] | deletion_compliance | 1.0000 | 41/1 | True |
| deletion | cortex[disable_dense] | evidence_resolution_rate | 1.0000 | 41/1 | True |
| deletion | cortex[disable_dense] | extraction_recall | 1.0000 | 41/1 | True |
| deletion | cortex[disable_dense] | extraction_spurious_rate | 0.6667 | 41/133 | False |
| deletion | cortex[disable_dense] | false_certainty_rate | 0.0000 | 41/48 | False |
| deletion | cortex[disable_dense] | lineage_completeness | 1.0000 | 41/1 | True |
| deletion | cortex[disable_dense] | mrr | 0.5854 | 41/156 | False |
| deletion | cortex[disable_dense] | ndcg_at_k | 0.6876 | 41/126 | False |
| deletion | cortex[disable_dense] | precision_at_k | 0.4878 | 41/171 | False |
| deletion | cortex[disable_dense] | provenance_coverage | 0.9756 | 41/9 | True |
| deletion | cortex[disable_dense] | recall_at_k | 0.9756 | 41/9 | True |
| deletion | cortex[disable_dense] | scope_accuracy | 0.0000 | 41/48 | False |
| deletion | cortex[disable_dense] | set_f1 | 0.6504 | 41/138 | False |
| deletion | cortex[disable_dense] | stale_leak_rate | 0.0000 | 41/48 | False |
| deletion | cortex[disable_dense] | supersession_accuracy | 1.0000 | 41/1 | True |
| deletion | cortex[disable_dense] | unsupported_claim_rate | 0.0000 | 41/48 | False |
| deletion | cortex[disable_evidence_ledger] | abstention_recall | 1.0000 | 41/1 | True |
| deletion | cortex[disable_evidence_ledger] | answer_support_recall | 0.0000 | 41/48 | False |
| deletion | cortex[disable_evidence_ledger] | contradiction_exposure_rate | 0.0000 | 41/48 | False |
| deletion | cortex[disable_evidence_ledger] | current_state_accuracy | 0.9756 | 41/9 | True |
| deletion | cortex[disable_evidence_ledger] | deletion_compliance | 1.0000 | 41/1 | True |
| deletion | cortex[disable_evidence_ledger] | evidence_resolution_rate | 0.0000 | 41/48 | False |
| deletion | cortex[disable_evidence_ledger] | extraction_recall | 1.0000 | 41/1 | True |
| deletion | cortex[disable_evidence_ledger] | extraction_spurious_rate | 0.6667 | 41/133 | False |
| deletion | cortex[disable_evidence_ledger] | false_certainty_rate | 1.0000 | 41/1 | True |
| deletion | cortex[disable_evidence_ledger] | lineage_completeness | 1.0000 | 41/1 | True |
| deletion | cortex[disable_evidence_ledger] | mrr | 0.5854 | 41/156 | False |
| deletion | cortex[disable_evidence_ledger] | ndcg_at_k | 0.6876 | 41/126 | False |
| deletion | cortex[disable_evidence_ledger] | precision_at_k | 0.4878 | 41/171 | False |
| deletion | cortex[disable_evidence_ledger] | provenance_coverage | 0.0000 | 41/48 | False |
| deletion | cortex[disable_evidence_ledger] | recall_at_k | 0.9756 | 41/9 | True |
| deletion | cortex[disable_evidence_ledger] | scope_accuracy | 0.0000 | 41/48 | False |
| deletion | cortex[disable_evidence_ledger] | set_f1 | 0.6504 | 41/138 | False |
| deletion | cortex[disable_evidence_ledger] | stale_leak_rate | 0.0000 | 41/48 | False |
| deletion | cortex[disable_evidence_ledger] | supersession_accuracy | 1.0000 | 41/1 | True |
| deletion | cortex[disable_evidence_ledger] | unsupported_claim_rate | 0.0000 | 41/48 | False |
| deletion | cortex[disable_graph_density] | abstention_recall | 1.0000 | 41/1 | True |
| deletion | cortex[disable_graph_density] | answer_support_recall | 0.9756 | 41/9 | True |
| deletion | cortex[disable_graph_density] | contradiction_exposure_rate | 0.0000 | 41/48 | False |
| deletion | cortex[disable_graph_density] | current_state_accuracy | 0.9756 | 41/9 | True |
| deletion | cortex[disable_graph_density] | deletion_compliance | 1.0000 | 41/1 | True |
| deletion | cortex[disable_graph_density] | evidence_resolution_rate | 1.0000 | 41/1 | True |
| deletion | cortex[disable_graph_density] | extraction_recall | 1.0000 | 41/1 | True |
| deletion | cortex[disable_graph_density] | extraction_spurious_rate | 0.6667 | 41/133 | False |
| deletion | cortex[disable_graph_density] | false_certainty_rate | 0.0000 | 41/48 | False |
| deletion | cortex[disable_graph_density] | lineage_completeness | 1.0000 | 41/1 | True |
| deletion | cortex[disable_graph_density] | mrr | 0.5854 | 41/156 | False |
| deletion | cortex[disable_graph_density] | ndcg_at_k | 0.6876 | 41/126 | False |
| deletion | cortex[disable_graph_density] | precision_at_k | 0.4878 | 41/171 | False |
| deletion | cortex[disable_graph_density] | provenance_coverage | 0.9756 | 41/9 | True |
| deletion | cortex[disable_graph_density] | recall_at_k | 0.9756 | 41/9 | True |
| deletion | cortex[disable_graph_density] | scope_accuracy | 0.0000 | 41/48 | False |
| deletion | cortex[disable_graph_density] | set_f1 | 0.6504 | 41/138 | False |
| deletion | cortex[disable_graph_density] | stale_leak_rate | 0.0000 | 41/48 | False |
| deletion | cortex[disable_graph_density] | supersession_accuracy | 1.0000 | 41/1 | True |
| deletion | cortex[disable_graph_density] | unsupported_claim_rate | 0.0000 | 41/48 | False |
| deletion | cortex[disable_supersession] | abstention_recall | 1.0000 | 41/1 | True |
| deletion | cortex[disable_supersession] | answer_support_recall | 0.9756 | 41/9 | True |
| deletion | cortex[disable_supersession] | contradiction_exposure_rate | 0.0000 | 41/48 | False |
| deletion | cortex[disable_supersession] | current_state_accuracy | 0.9756 | 41/9 | True |
| deletion | cortex[disable_supersession] | deletion_compliance | 1.0000 | 41/1 | True |
| deletion | cortex[disable_supersession] | evidence_resolution_rate | 1.0000 | 41/1 | True |
| deletion | cortex[disable_supersession] | extraction_recall | 1.0000 | 41/1 | True |
| deletion | cortex[disable_supersession] | extraction_spurious_rate | 0.6667 | 41/133 | False |
| deletion | cortex[disable_supersession] | false_certainty_rate | 0.0000 | 41/48 | False |
| deletion | cortex[disable_supersession] | lineage_completeness | 0.5122 | 41/168 | False |
| deletion | cortex[disable_supersession] | mrr | 0.5854 | 41/156 | False |
| deletion | cortex[disable_supersession] | ndcg_at_k | 0.6876 | 41/126 | False |
| deletion | cortex[disable_supersession] | precision_at_k | 0.4878 | 41/171 | False |
| deletion | cortex[disable_supersession] | provenance_coverage | 0.9756 | 41/9 | True |
| deletion | cortex[disable_supersession] | recall_at_k | 0.9756 | 41/9 | True |
| deletion | cortex[disable_supersession] | scope_accuracy | 0.0000 | 41/48 | False |
| deletion | cortex[disable_supersession] | set_f1 | 0.6504 | 41/138 | False |
| deletion | cortex[disable_supersession] | stale_leak_rate | 0.0000 | 41/48 | False |
| deletion | cortex[disable_supersession] | supersession_accuracy | 1.0000 | 41/1 | True |
| deletion | cortex[disable_supersession] | unsupported_claim_rate | 0.0000 | 41/48 | False |
| deletion | raw_context | abstention_recall | 1.0000 | 41/1 | True |
| deletion | raw_context | answer_support_recall | 1.0000 | 41/1 | True |
| deletion | raw_context | contradiction_exposure_rate | 0.0000 | 41/48 | False |
| deletion | raw_context | current_state_accuracy | 1.0000 | 41/1 | True |
| deletion | raw_context | deletion_compliance | 0.0000 | 41/48 | False |
| deletion | raw_context | evidence_resolution_rate | 1.0000 | 41/1 | True |
| deletion | raw_context | false_certainty_rate | 0.0000 | 41/48 | False |
| deletion | raw_context | lineage_completeness | 1.0000 | 41/1 | True |
| deletion | raw_context | mrr | 0.5000 | 41/170 | False |
| deletion | raw_context | ndcg_at_k | 0.6309 | 41/144 | False |
| deletion | raw_context | precision_at_k | 0.2520 | 41/153 | False |
| deletion | raw_context | provenance_coverage | 1.0000 | 41/1 | True |
| deletion | raw_context | recall_at_k | 1.0000 | 41/1 | True |
| deletion | raw_context | scope_accuracy | 0.0000 | 41/48 | False |
| deletion | raw_context | set_f1 | 0.4024 | 41/173 | False |
| deletion | raw_context | stale_leak_rate | 1.0000 | 41/1 | True |
| deletion | raw_context | supersession_accuracy | 0.0000 | 41/48 | False |
| deletion | raw_context | unsupported_claim_rate | 0.0000 | 41/48 | False |
| exact_recall | bm25 | abstention_recall | 1.0000 | 43/1 | True |
| exact_recall | bm25 | answer_support_recall | 1.0000 | 43/1 | True |
| exact_recall | bm25 | contradiction_exposure_rate | 0.0000 | 43/48 | False |
| exact_recall | bm25 | current_state_accuracy | 1.0000 | 43/1 | True |
| exact_recall | bm25 | deletion_compliance | 1.0000 | 43/1 | True |
| exact_recall | bm25 | evidence_resolution_rate | 1.0000 | 43/1 | True |
| exact_recall | bm25 | false_certainty_rate | 0.0000 | 43/48 | False |
| exact_recall | bm25 | lineage_completeness | 1.0000 | 43/1 | True |
| exact_recall | bm25 | mrr | 1.0000 | 43/1 | True |
| exact_recall | bm25 | ndcg_at_k | 1.0000 | 43/1 | True |
| exact_recall | bm25 | precision_at_k | 0.5349 | 43/165 | False |
| exact_recall | bm25 | provenance_coverage | 1.0000 | 43/1 | True |
| exact_recall | bm25 | recall_at_k | 1.0000 | 43/1 | True |
| exact_recall | bm25 | scope_accuracy | 0.0698 | 43/86 | False |
| exact_recall | bm25 | set_f1 | 0.6899 | 43/125 | False |
| exact_recall | bm25 | stale_leak_rate | 0.0000 | 43/48 | False |
| exact_recall | bm25 | supersession_accuracy | 1.0000 | 43/1 | True |
| exact_recall | bm25 | unsupported_claim_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex | abstention_recall | 1.0000 | 43/1 | True |
| exact_recall | cortex | answer_support_recall | 1.0000 | 43/1 | True |
| exact_recall | cortex | contradiction_exposure_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex | current_state_accuracy | 1.0000 | 43/1 | True |
| exact_recall | cortex | deletion_compliance | 1.0000 | 43/1 | True |
| exact_recall | cortex | evidence_resolution_rate | 1.0000 | 43/1 | True |
| exact_recall | cortex | extraction_recall | 1.0000 | 43/1 | True |
| exact_recall | cortex | extraction_spurious_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex | false_certainty_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex | lineage_completeness | 1.0000 | 43/1 | True |
| exact_recall | cortex | mrr | 1.0000 | 43/1 | True |
| exact_recall | cortex | ndcg_at_k | 1.0000 | 43/1 | True |
| exact_recall | cortex | precision_at_k | 1.0000 | 43/1 | True |
| exact_recall | cortex | provenance_coverage | 1.0000 | 43/1 | True |
| exact_recall | cortex | recall_at_k | 1.0000 | 43/1 | True |
| exact_recall | cortex | scope_accuracy | 1.0000 | 43/1 | True |
| exact_recall | cortex | set_f1 | 1.0000 | 43/1 | True |
| exact_recall | cortex | stale_leak_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex | supersession_accuracy | 1.0000 | 43/1 | True |
| exact_recall | cortex | unsupported_claim_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_authority] | abstention_recall | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_authority] | answer_support_recall | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_authority] | contradiction_exposure_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_authority] | current_state_accuracy | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_authority] | deletion_compliance | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_authority] | evidence_resolution_rate | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_authority] | extraction_recall | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_authority] | extraction_spurious_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_authority] | false_certainty_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_authority] | lineage_completeness | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_authority] | mrr | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_authority] | ndcg_at_k | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_authority] | precision_at_k | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_authority] | provenance_coverage | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_authority] | recall_at_k | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_authority] | scope_accuracy | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_authority] | set_f1 | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_authority] | stale_leak_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_authority] | supersession_accuracy | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_authority] | unsupported_claim_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_contradiction_penalty] | abstention_recall | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_contradiction_penalty] | answer_support_recall | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_contradiction_penalty] | contradiction_exposure_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_contradiction_penalty] | current_state_accuracy | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_contradiction_penalty] | deletion_compliance | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_contradiction_penalty] | evidence_resolution_rate | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_contradiction_penalty] | extraction_recall | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_contradiction_penalty] | extraction_spurious_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_contradiction_penalty] | false_certainty_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_contradiction_penalty] | lineage_completeness | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_contradiction_penalty] | mrr | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_contradiction_penalty] | ndcg_at_k | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_contradiction_penalty] | precision_at_k | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_contradiction_penalty] | provenance_coverage | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_contradiction_penalty] | recall_at_k | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_contradiction_penalty] | scope_accuracy | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_contradiction_penalty] | set_f1 | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_contradiction_penalty] | stale_leak_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_contradiction_penalty] | supersession_accuracy | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_contradiction_penalty] | unsupported_claim_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_dense] | abstention_recall | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_dense] | answer_support_recall | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_dense] | contradiction_exposure_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_dense] | current_state_accuracy | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_dense] | deletion_compliance | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_dense] | evidence_resolution_rate | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_dense] | extraction_recall | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_dense] | extraction_spurious_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_dense] | false_certainty_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_dense] | lineage_completeness | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_dense] | mrr | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_dense] | ndcg_at_k | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_dense] | precision_at_k | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_dense] | provenance_coverage | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_dense] | recall_at_k | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_dense] | scope_accuracy | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_dense] | set_f1 | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_dense] | stale_leak_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_dense] | supersession_accuracy | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_dense] | unsupported_claim_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_evidence_ledger] | abstention_recall | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_evidence_ledger] | answer_support_recall | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_evidence_ledger] | contradiction_exposure_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_evidence_ledger] | current_state_accuracy | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_evidence_ledger] | deletion_compliance | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_evidence_ledger] | evidence_resolution_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_evidence_ledger] | extraction_recall | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_evidence_ledger] | extraction_spurious_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_evidence_ledger] | false_certainty_rate | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_evidence_ledger] | lineage_completeness | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_evidence_ledger] | mrr | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_evidence_ledger] | ndcg_at_k | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_evidence_ledger] | precision_at_k | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_evidence_ledger] | provenance_coverage | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_evidence_ledger] | recall_at_k | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_evidence_ledger] | scope_accuracy | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_evidence_ledger] | set_f1 | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_evidence_ledger] | stale_leak_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_evidence_ledger] | supersession_accuracy | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_evidence_ledger] | unsupported_claim_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_graph_density] | abstention_recall | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_graph_density] | answer_support_recall | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_graph_density] | contradiction_exposure_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_graph_density] | current_state_accuracy | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_graph_density] | deletion_compliance | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_graph_density] | evidence_resolution_rate | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_graph_density] | extraction_recall | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_graph_density] | extraction_spurious_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_graph_density] | false_certainty_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_graph_density] | lineage_completeness | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_graph_density] | mrr | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_graph_density] | ndcg_at_k | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_graph_density] | precision_at_k | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_graph_density] | provenance_coverage | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_graph_density] | recall_at_k | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_graph_density] | scope_accuracy | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_graph_density] | set_f1 | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_graph_density] | stale_leak_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_graph_density] | supersession_accuracy | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_graph_density] | unsupported_claim_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_supersession] | abstention_recall | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_supersession] | answer_support_recall | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_supersession] | contradiction_exposure_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_supersession] | current_state_accuracy | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_supersession] | deletion_compliance | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_supersession] | evidence_resolution_rate | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_supersession] | extraction_recall | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_supersession] | extraction_spurious_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_supersession] | false_certainty_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_supersession] | lineage_completeness | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_supersession] | mrr | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_supersession] | ndcg_at_k | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_supersession] | precision_at_k | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_supersession] | provenance_coverage | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_supersession] | recall_at_k | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_supersession] | scope_accuracy | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_supersession] | set_f1 | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_supersession] | stale_leak_rate | 0.0000 | 43/48 | False |
| exact_recall | cortex[disable_supersession] | supersession_accuracy | 1.0000 | 43/1 | True |
| exact_recall | cortex[disable_supersession] | unsupported_claim_rate | 0.0000 | 43/48 | False |
| exact_recall | raw_context | abstention_recall | 1.0000 | 43/1 | True |
| exact_recall | raw_context | answer_support_recall | 1.0000 | 43/1 | True |
| exact_recall | raw_context | contradiction_exposure_rate | 0.0000 | 43/48 | False |
| exact_recall | raw_context | current_state_accuracy | 1.0000 | 43/1 | True |
| exact_recall | raw_context | deletion_compliance | 1.0000 | 43/1 | True |
| exact_recall | raw_context | evidence_resolution_rate | 1.0000 | 43/1 | True |
| exact_recall | raw_context | false_certainty_rate | 0.0000 | 43/48 | False |
| exact_recall | raw_context | lineage_completeness | 1.0000 | 43/1 | True |
| exact_recall | raw_context | mrr | 1.0000 | 43/1 | True |
| exact_recall | raw_context | ndcg_at_k | 1.0000 | 43/1 | True |
| exact_recall | raw_context | precision_at_k | 0.3682 | 43/171 | False |
| exact_recall | raw_context | provenance_coverage | 1.0000 | 43/1 | True |
| exact_recall | raw_context | recall_at_k | 1.0000 | 43/1 | True |
| exact_recall | raw_context | scope_accuracy | 0.0465 | 43/74 | False |
| exact_recall | raw_context | set_f1 | 0.5271 | 43/166 | False |
| exact_recall | raw_context | stale_leak_rate | 0.0000 | 43/48 | False |
| exact_recall | raw_context | supersession_accuracy | 1.0000 | 43/1 | True |
| exact_recall | raw_context | unsupported_claim_rate | 0.0000 | 43/48 | False |
| tracking | bm25 | abstention_recall | 1.0000 | 42/1 | True |
| tracking | bm25 | answer_support_recall | 1.0000 | 42/1 | True |
| tracking | bm25 | contradiction_exposure_rate | 0.0000 | 42/48 | False |
| tracking | bm25 | current_state_accuracy | 1.0000 | 42/1 | True |
| tracking | bm25 | deletion_compliance | 0.0000 | 42/48 | False |
| tracking | bm25 | evidence_resolution_rate | 1.0000 | 42/1 | True |
| tracking | bm25 | false_certainty_rate | 0.0000 | 42/48 | False |
| tracking | bm25 | lineage_completeness | 1.0000 | 42/1 | True |
| tracking | bm25 | mrr | 0.6190 | 42/147 | False |
| tracking | bm25 | ndcg_at_k | 0.7188 | 42/114 | False |
| tracking | bm25 | precision_at_k | 0.5000 | 42/170 | False |
| tracking | bm25 | provenance_coverage | 1.0000 | 42/1 | True |
| tracking | bm25 | recall_at_k | 1.0000 | 42/1 | True |
| tracking | bm25 | scope_accuracy | 0.0000 | 42/48 | False |
| tracking | bm25 | set_f1 | 0.6667 | 42/133 | False |
| tracking | bm25 | stale_leak_rate | 1.0000 | 42/1 | True |
| tracking | bm25 | supersession_accuracy | 0.0000 | 42/48 | False |
| tracking | bm25 | unsupported_claim_rate | 0.0000 | 42/48 | False |
| tracking | cortex | abstention_recall | 1.0000 | 42/1 | True |
| tracking | cortex | answer_support_recall | 1.0000 | 42/1 | True |
| tracking | cortex | contradiction_exposure_rate | 0.0000 | 42/48 | False |
| tracking | cortex | current_state_accuracy | 1.0000 | 42/1 | True |
| tracking | cortex | deletion_compliance | 1.0000 | 42/1 | True |
| tracking | cortex | evidence_resolution_rate | 1.0000 | 42/1 | True |
| tracking | cortex | extraction_recall | 1.0000 | 42/1 | True |
| tracking | cortex | extraction_spurious_rate | 0.5000 | 42/170 | False |
| tracking | cortex | false_certainty_rate | 0.0000 | 42/48 | False |
| tracking | cortex | lineage_completeness | 1.0000 | 42/1 | True |
| tracking | cortex | mrr | 1.0000 | 42/1 | True |
| tracking | cortex | ndcg_at_k | 1.0000 | 42/1 | True |
| tracking | cortex | precision_at_k | 1.0000 | 42/1 | True |
| tracking | cortex | provenance_coverage | 1.0000 | 42/1 | True |
| tracking | cortex | recall_at_k | 1.0000 | 42/1 | True |
| tracking | cortex | scope_accuracy | 1.0000 | 42/1 | True |
| tracking | cortex | set_f1 | 1.0000 | 42/1 | True |
| tracking | cortex | stale_leak_rate | 0.0000 | 42/48 | False |
| tracking | cortex | supersession_accuracy | 1.0000 | 42/1 | True |
| tracking | cortex | unsupported_claim_rate | 0.0000 | 42/48 | False |
| tracking | cortex[disable_authority] | abstention_recall | 1.0000 | 42/1 | True |
| tracking | cortex[disable_authority] | answer_support_recall | 1.0000 | 42/1 | True |
| tracking | cortex[disable_authority] | contradiction_exposure_rate | 0.0000 | 42/48 | False |
| tracking | cortex[disable_authority] | current_state_accuracy | 1.0000 | 42/1 | True |
| tracking | cortex[disable_authority] | deletion_compliance | 1.0000 | 42/1 | True |
| tracking | cortex[disable_authority] | evidence_resolution_rate | 1.0000 | 42/1 | True |
| tracking | cortex[disable_authority] | extraction_recall | 1.0000 | 42/1 | True |
| tracking | cortex[disable_authority] | extraction_spurious_rate | 0.5000 | 42/170 | False |
| tracking | cortex[disable_authority] | false_certainty_rate | 0.0000 | 42/48 | False |
| tracking | cortex[disable_authority] | lineage_completeness | 1.0000 | 42/1 | True |
| tracking | cortex[disable_authority] | mrr | 1.0000 | 42/1 | True |
| tracking | cortex[disable_authority] | ndcg_at_k | 1.0000 | 42/1 | True |
| tracking | cortex[disable_authority] | precision_at_k | 1.0000 | 42/1 | True |
| tracking | cortex[disable_authority] | provenance_coverage | 1.0000 | 42/1 | True |
| tracking | cortex[disable_authority] | recall_at_k | 1.0000 | 42/1 | True |
| tracking | cortex[disable_authority] | scope_accuracy | 1.0000 | 42/1 | True |
| tracking | cortex[disable_authority] | set_f1 | 1.0000 | 42/1 | True |
| tracking | cortex[disable_authority] | stale_leak_rate | 0.0000 | 42/48 | False |
| tracking | cortex[disable_authority] | supersession_accuracy | 1.0000 | 42/1 | True |
| tracking | cortex[disable_authority] | unsupported_claim_rate | 0.0000 | 42/48 | False |
| tracking | cortex[disable_contradiction_penalty] | abstention_recall | 1.0000 | 42/1 | True |
| tracking | cortex[disable_contradiction_penalty] | answer_support_recall | 1.0000 | 42/1 | True |
| tracking | cortex[disable_contradiction_penalty] | contradiction_exposure_rate | 0.0000 | 42/48 | False |
| tracking | cortex[disable_contradiction_penalty] | current_state_accuracy | 1.0000 | 42/1 | True |
| tracking | cortex[disable_contradiction_penalty] | deletion_compliance | 1.0000 | 42/1 | True |
| tracking | cortex[disable_contradiction_penalty] | evidence_resolution_rate | 1.0000 | 42/1 | True |
| tracking | cortex[disable_contradiction_penalty] | extraction_recall | 1.0000 | 42/1 | True |
| tracking | cortex[disable_contradiction_penalty] | extraction_spurious_rate | 0.5000 | 42/170 | False |
| tracking | cortex[disable_contradiction_penalty] | false_certainty_rate | 0.0000 | 42/48 | False |
| tracking | cortex[disable_contradiction_penalty] | lineage_completeness | 1.0000 | 42/1 | True |
| tracking | cortex[disable_contradiction_penalty] | mrr | 1.0000 | 42/1 | True |
| tracking | cortex[disable_contradiction_penalty] | ndcg_at_k | 1.0000 | 42/1 | True |
| tracking | cortex[disable_contradiction_penalty] | precision_at_k | 1.0000 | 42/1 | True |
| tracking | cortex[disable_contradiction_penalty] | provenance_coverage | 1.0000 | 42/1 | True |
| tracking | cortex[disable_contradiction_penalty] | recall_at_k | 1.0000 | 42/1 | True |
| tracking | cortex[disable_contradiction_penalty] | scope_accuracy | 1.0000 | 42/1 | True |
| tracking | cortex[disable_contradiction_penalty] | set_f1 | 1.0000 | 42/1 | True |
| tracking | cortex[disable_contradiction_penalty] | stale_leak_rate | 0.0000 | 42/48 | False |
| tracking | cortex[disable_contradiction_penalty] | supersession_accuracy | 1.0000 | 42/1 | True |
| tracking | cortex[disable_contradiction_penalty] | unsupported_claim_rate | 0.0000 | 42/48 | False |
| tracking | cortex[disable_dense] | abstention_recall | 1.0000 | 42/1 | True |
| tracking | cortex[disable_dense] | answer_support_recall | 1.0000 | 42/1 | True |
| tracking | cortex[disable_dense] | contradiction_exposure_rate | 0.0000 | 42/48 | False |
| tracking | cortex[disable_dense] | current_state_accuracy | 1.0000 | 42/1 | True |
| tracking | cortex[disable_dense] | deletion_compliance | 1.0000 | 42/1 | True |
| tracking | cortex[disable_dense] | evidence_resolution_rate | 1.0000 | 42/1 | True |
| tracking | cortex[disable_dense] | extraction_recall | 1.0000 | 42/1 | True |
| tracking | cortex[disable_dense] | extraction_spurious_rate | 0.5000 | 42/170 | False |
| tracking | cortex[disable_dense] | false_certainty_rate | 0.0000 | 42/48 | False |
| tracking | cortex[disable_dense] | lineage_completeness | 1.0000 | 42/1 | True |
| tracking | cortex[disable_dense] | mrr | 1.0000 | 42/1 | True |
| tracking | cortex[disable_dense] | ndcg_at_k | 1.0000 | 42/1 | True |
| tracking | cortex[disable_dense] | precision_at_k | 1.0000 | 42/1 | True |
| tracking | cortex[disable_dense] | provenance_coverage | 1.0000 | 42/1 | True |
| tracking | cortex[disable_dense] | recall_at_k | 1.0000 | 42/1 | True |
| tracking | cortex[disable_dense] | scope_accuracy | 1.0000 | 42/1 | True |
| tracking | cortex[disable_dense] | set_f1 | 1.0000 | 42/1 | True |
| tracking | cortex[disable_dense] | stale_leak_rate | 0.0000 | 42/48 | False |
| tracking | cortex[disable_dense] | supersession_accuracy | 1.0000 | 42/1 | True |
| tracking | cortex[disable_dense] | unsupported_claim_rate | 0.0000 | 42/48 | False |
| tracking | cortex[disable_evidence_ledger] | abstention_recall | 1.0000 | 42/1 | True |
| tracking | cortex[disable_evidence_ledger] | answer_support_recall | 0.0000 | 42/48 | False |
| tracking | cortex[disable_evidence_ledger] | contradiction_exposure_rate | 0.0000 | 42/48 | False |
| tracking | cortex[disable_evidence_ledger] | current_state_accuracy | 1.0000 | 42/1 | True |
| tracking | cortex[disable_evidence_ledger] | deletion_compliance | 1.0000 | 42/1 | True |
| tracking | cortex[disable_evidence_ledger] | evidence_resolution_rate | 0.0000 | 42/48 | False |
| tracking | cortex[disable_evidence_ledger] | extraction_recall | 1.0000 | 42/1 | True |
| tracking | cortex[disable_evidence_ledger] | extraction_spurious_rate | 0.5000 | 42/170 | False |
| tracking | cortex[disable_evidence_ledger] | false_certainty_rate | 1.0000 | 42/1 | True |
| tracking | cortex[disable_evidence_ledger] | lineage_completeness | 1.0000 | 42/1 | True |
| tracking | cortex[disable_evidence_ledger] | mrr | 1.0000 | 42/1 | True |
| tracking | cortex[disable_evidence_ledger] | ndcg_at_k | 1.0000 | 42/1 | True |
| tracking | cortex[disable_evidence_ledger] | precision_at_k | 1.0000 | 42/1 | True |
| tracking | cortex[disable_evidence_ledger] | provenance_coverage | 0.0000 | 42/48 | False |
| tracking | cortex[disable_evidence_ledger] | recall_at_k | 1.0000 | 42/1 | True |
| tracking | cortex[disable_evidence_ledger] | scope_accuracy | 1.0000 | 42/1 | True |
| tracking | cortex[disable_evidence_ledger] | set_f1 | 1.0000 | 42/1 | True |
| tracking | cortex[disable_evidence_ledger] | stale_leak_rate | 0.0000 | 42/48 | False |
| tracking | cortex[disable_evidence_ledger] | supersession_accuracy | 1.0000 | 42/1 | True |
| tracking | cortex[disable_evidence_ledger] | unsupported_claim_rate | 0.0000 | 42/48 | False |
| tracking | cortex[disable_graph_density] | abstention_recall | 1.0000 | 42/1 | True |
| tracking | cortex[disable_graph_density] | answer_support_recall | 1.0000 | 42/1 | True |
| tracking | cortex[disable_graph_density] | contradiction_exposure_rate | 0.0000 | 42/48 | False |
| tracking | cortex[disable_graph_density] | current_state_accuracy | 1.0000 | 42/1 | True |
| tracking | cortex[disable_graph_density] | deletion_compliance | 1.0000 | 42/1 | True |
| tracking | cortex[disable_graph_density] | evidence_resolution_rate | 1.0000 | 42/1 | True |
| tracking | cortex[disable_graph_density] | extraction_recall | 1.0000 | 42/1 | True |
| tracking | cortex[disable_graph_density] | extraction_spurious_rate | 0.5000 | 42/170 | False |
| tracking | cortex[disable_graph_density] | false_certainty_rate | 0.0000 | 42/48 | False |
| tracking | cortex[disable_graph_density] | lineage_completeness | 1.0000 | 42/1 | True |
| tracking | cortex[disable_graph_density] | mrr | 1.0000 | 42/1 | True |
| tracking | cortex[disable_graph_density] | ndcg_at_k | 1.0000 | 42/1 | True |
| tracking | cortex[disable_graph_density] | precision_at_k | 1.0000 | 42/1 | True |
| tracking | cortex[disable_graph_density] | provenance_coverage | 1.0000 | 42/1 | True |
| tracking | cortex[disable_graph_density] | recall_at_k | 1.0000 | 42/1 | True |
| tracking | cortex[disable_graph_density] | scope_accuracy | 1.0000 | 42/1 | True |
| tracking | cortex[disable_graph_density] | set_f1 | 1.0000 | 42/1 | True |
| tracking | cortex[disable_graph_density] | stale_leak_rate | 0.0000 | 42/48 | False |
| tracking | cortex[disable_graph_density] | supersession_accuracy | 1.0000 | 42/1 | True |
| tracking | cortex[disable_graph_density] | unsupported_claim_rate | 0.0000 | 42/48 | False |
| tracking | cortex[disable_supersession] | abstention_recall | 1.0000 | 42/1 | True |
| tracking | cortex[disable_supersession] | answer_support_recall | 1.0000 | 42/1 | True |
| tracking | cortex[disable_supersession] | contradiction_exposure_rate | 0.0000 | 42/48 | False |
| tracking | cortex[disable_supersession] | current_state_accuracy | 1.0000 | 42/1 | True |
| tracking | cortex[disable_supersession] | deletion_compliance | 0.0000 | 42/48 | False |
| tracking | cortex[disable_supersession] | evidence_resolution_rate | 1.0000 | 42/1 | True |
| tracking | cortex[disable_supersession] | extraction_recall | 1.0000 | 42/1 | True |
| tracking | cortex[disable_supersession] | extraction_spurious_rate | 0.5000 | 42/170 | False |
| tracking | cortex[disable_supersession] | false_certainty_rate | 0.0000 | 42/48 | False |
| tracking | cortex[disable_supersession] | lineage_completeness | 0.0000 | 42/48 | False |
| tracking | cortex[disable_supersession] | mrr | 0.5119 | 42/168 | False |
| tracking | cortex[disable_supersession] | ndcg_at_k | 0.6397 | 42/142 | False |
| tracking | cortex[disable_supersession] | precision_at_k | 0.5000 | 42/170 | False |
| tracking | cortex[disable_supersession] | provenance_coverage | 1.0000 | 42/1 | True |
| tracking | cortex[disable_supersession] | recall_at_k | 1.0000 | 42/1 | True |
| tracking | cortex[disable_supersession] | scope_accuracy | 0.0000 | 42/48 | False |
| tracking | cortex[disable_supersession] | set_f1 | 0.6667 | 42/133 | False |
| tracking | cortex[disable_supersession] | stale_leak_rate | 1.0000 | 42/1 | True |
| tracking | cortex[disable_supersession] | supersession_accuracy | 0.0000 | 42/48 | False |
| tracking | cortex[disable_supersession] | unsupported_claim_rate | 0.0000 | 42/48 | False |
| tracking | raw_context | abstention_recall | 1.0000 | 42/1 | True |
| tracking | raw_context | answer_support_recall | 1.0000 | 42/1 | True |
| tracking | raw_context | contradiction_exposure_rate | 0.0000 | 42/48 | False |
| tracking | raw_context | current_state_accuracy | 1.0000 | 42/1 | True |
| tracking | raw_context | deletion_compliance | 0.0000 | 42/48 | False |
| tracking | raw_context | evidence_resolution_rate | 1.0000 | 42/1 | True |
| tracking | raw_context | false_certainty_rate | 0.0000 | 42/48 | False |
| tracking | raw_context | lineage_completeness | 1.0000 | 42/1 | True |
| tracking | raw_context | mrr | 0.5000 | 42/170 | False |
| tracking | raw_context | ndcg_at_k | 0.6309 | 42/144 | False |
| tracking | raw_context | precision_at_k | 0.3413 | 42/169 | False |
| tracking | raw_context | provenance_coverage | 1.0000 | 42/1 | True |
| tracking | raw_context | recall_at_k | 1.0000 | 42/1 | True |
| tracking | raw_context | scope_accuracy | 0.0000 | 42/48 | False |
| tracking | raw_context | set_f1 | 0.5079 | 42/169 | False |
| tracking | raw_context | stale_leak_rate | 1.0000 | 42/1 | True |
| tracking | raw_context | supersession_accuracy | 0.0000 | 42/48 | False |
| tracking | raw_context | unsupported_claim_rate | 0.0000 | 42/48 | False |

## Estratificação da amostra (plano §9.1)

Contagem de casos únicos por eixo — uma média única nunca revela se a amostra está concentrada em um hop, tamanho de histórico ou carga de filler.

| Eixo | Bucket | n (casos) |
|---|---|---:|
| task_type | absence | 42 |
| task_type | aggregation | 41 |
| task_type | cascade | 41 |
| task_type | deletion | 41 |
| task_type | exact_recall | 43 |
| task_type | tracking | 42 |
| hop | 0 | 246 |
| hop | 1 | 3 |
| hop | 2 | 1 |
| history_size | s | 246 |
| history_size | xs | 4 |
| filler | nofiller | 250 |

## Comparação pareada (cortex − baseline)

MDE pré-registrado: 0.15. Confirmatório exige n ≥ `required_n`. `holm` marca rejeição após correção dentro da família.

| Métrica | Baseline | n | req n | diff | IC95 | p | holm |
|---|---|---:|---:|---:|---|---:|---|
| cortex_vs_bm25 | abstention_recall | 250 | 58 | +0.1680 | [+0.1280, +0.2160] | 0.0005 | True |
| cortex_vs_raw_context | abstention_recall | 250 | 58 | +0.1680 | [+0.1280, +0.2160] | 0.0005 | True |
| cortex_vs_bm25 | answer_support_recall | 250 | 58 | -0.0040 | [-0.0120, +0.0000] | 0.6175 | False |
| cortex_vs_raw_context | answer_support_recall | 250 | 58 | -0.0040 | [-0.0120, +0.0000] | 0.6175 | False |
| cortex_vs_bm25 | cascade_correctness_hop1 | 41 | 48 | +1.0000 | [+1.0000, +1.0000] | 0.0005 | True |
| cortex_vs_raw_context | cascade_correctness_hop1 | 41 | 48 | +1.0000 | [+1.0000, +1.0000] | 0.0005 | True |
| cortex_vs_bm25 | cascade_correctness_hop2 | 41 | 48 | +1.0000 | [+1.0000, +1.0000] | 0.0005 | True |
| cortex_vs_raw_context | cascade_correctness_hop2 | 41 | 48 | +1.0000 | [+1.0000, +1.0000] | 0.0005 | True |
| cortex_vs_bm25 | contradiction_exposure_rate | 250 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_raw_context | contradiction_exposure_rate | 250 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_bm25 | current_state_accuracy | 250 | 1 | -0.0040 | [-0.0120, +0.0000] | 0.6175 | False |
| cortex_vs_raw_context | current_state_accuracy | 250 | 1 | -0.0040 | [-0.0120, +0.0000] | 0.6175 | False |
| cortex_vs_bm25 | deletion_compliance | 250 | 169 | +0.4960 | [+0.4320, +0.5560] | 0.0005 | True |
| cortex_vs_raw_context | deletion_compliance | 250 | 169 | +0.4960 | [+0.4320, +0.5560] | 0.0005 | True |
| cortex_vs_bm25 | evidence_resolution_rate | 250 | 1 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_raw_context | evidence_resolution_rate | 250 | 1 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_bm25 | false_certainty_rate | 250 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_raw_context | false_certainty_rate | 250 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_bm25 | lineage_completeness | 250 | 1 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_raw_context | lineage_completeness | 250 | 1 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_bm25 | mrr | 250 | 143 | +0.0620 | [+0.0420, +0.0860] | 0.0005 | True |
| cortex_vs_raw_context | mrr | 250 | 156 | +0.1140 | [+0.0880, +0.1440] | 0.0005 | True |
| cortex_vs_bm25 | ndcg_at_k | 250 | 126 | +0.0447 | [+0.0293, +0.0624] | 0.0005 | True |
| cortex_vs_raw_context | ndcg_at_k | 250 | 139 | +0.0831 | [+0.0635, +0.1048] | 0.0005 | True |
| cortex_vs_bm25 | precision_at_k | 250 | 173 | +0.2167 | [+0.1920, +0.2433] | 0.0005 | True |
| cortex_vs_raw_context | precision_at_k | 250 | 167 | +0.3387 | [+0.3097, +0.3687] | 0.0005 | True |
| cortex_vs_bm25 | provenance_coverage | 250 | 1 | -0.0040 | [-0.0120, +0.0000] | 0.6175 | False |
| cortex_vs_raw_context | provenance_coverage | 250 | 1 | -0.0040 | [-0.0120, +0.0000] | 0.6175 | False |
| cortex_vs_bm25 | recall_at_k | 250 | 58 | -0.0040 | [-0.0120, +0.0000] | 0.6175 | False |
| cortex_vs_raw_context | recall_at_k | 250 | 58 | -0.0040 | [-0.0120, +0.0000] | 0.6175 | False |
| cortex_vs_bm25 | scope_accuracy | 250 | 168 | +0.3360 | [+0.2800, +0.3920] | 0.0005 | True |
| cortex_vs_raw_context | scope_accuracy | 250 | 55 | +0.6600 | [+0.6040, +0.7160] | 0.0005 | True |
| cortex_vs_bm25 | set_f1 | 250 | 114 | +0.1693 | [+0.1500, +0.1893] | 0.0005 | True |
| cortex_vs_raw_context | set_f1 | 250 | 173 | +0.4389 | [+0.4060, +0.4777] | 0.0005 | True |
| cortex_vs_bm25 | stale_leak_rate | 250 | 170 | -0.4960 | [-0.5560, -0.4320] | 0.0005 | True |
| cortex_vs_raw_context | stale_leak_rate | 250 | 170 | -0.4960 | [-0.5560, -0.4320] | 0.0005 | True |
| cortex_vs_bm25 | supersession_accuracy | 250 | 169 | +0.4960 | [+0.4320, +0.5560] | 0.0005 | True |
| cortex_vs_raw_context | supersession_accuracy | 250 | 169 | +0.4960 | [+0.4320, +0.5560] | 0.0005 | True |
| cortex_vs_bm25 | unsupported_claim_rate | 250 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |
| cortex_vs_raw_context | unsupported_claim_rate | 250 | 48 | +0.0000 | [+0.0000, +0.0000] | 1.0000 | False |

### Correção de múltiplas hipóteses (Holm-Bonferroni, por família)

| Família | Comparações | Rejeitadas | menor p | maior p |
|---|---:|---:|---:|---:|
| abstention | 4 | 2 | 0.0005 | 1.0000 |
| evidence | 6 | 0 | 0.6175 | 1.0000 |
| retrieval | 14 | 10 | 0.0005 | 0.6175 |
| temporality | 16 | 10 | 0.0005 | 1.0000 |

## Gates

### G0_reproducibility
- explicit_errors: 0
- leakage_events: 0
- clean: True

### G1_cortex_integrity
- stale_leak_rate_cortex: 0.0
- stale_leak_rate_bm25: 0.496
- stale_leak_rate_raw_context: 0.496
- stale_leak_not_worse_than_bm25: True
- stale_leak_not_worse_than_raw_context: True
- paired_interval_available: True
- exceptions_converted_to_zero: 0

### G2_relative_value
- set_f1: {'comparison': 'cortex_vs_raw_context', 'holm_significant': True, 'n': 250, 'diff': 0.43885714344000004, 'ci_low': 0.40596190528, 'ci_high': 0.47765714348, 'ci_includes_zero': False, 'family': 'retrieval', 'required_n': 173, 'minimum_detectable_effect': 0.15, 'power_basis': 'baseline_arm', 'p_value': 0.0005, 'confirmatory': True}
- current_state_accuracy: {'comparison': 'cortex_vs_bm25', 'holm_significant': False, 'n': 250, 'diff': -0.004, 'ci_low': -0.012, 'ci_high': 0.0, 'ci_includes_zero': True, 'family': 'temporality', 'required_n': 1, 'minimum_detectable_effect': 0.15, 'power_basis': 'baseline_arm', 'p_value': 0.6175, 'confirmatory': True}
- deletion_compliance: {'comparison': 'cortex_vs_bm25', 'holm_significant': True, 'n': 250, 'diff': 0.496, 'ci_low': 0.432, 'ci_high': 0.556, 'ci_includes_zero': False, 'family': 'temporality', 'required_n': 169, 'minimum_detectable_effect': 0.15, 'power_basis': 'baseline_arm', 'p_value': 0.0005, 'confirmatory': True}
- abstention_recall: {'comparison': 'cortex_vs_bm25', 'holm_significant': True, 'n': 250, 'diff': 0.168, 'ci_low': 0.128, 'ci_high': 0.216, 'ci_includes_zero': False, 'family': 'abstention', 'required_n': 58, 'minimum_detectable_effect': 0.15, 'power_basis': 'baseline_arm', 'p_value': 0.0005, 'confirmatory': True}
- recall_at_k: {'comparison': 'cortex_vs_bm25', 'holm_significant': False, 'n': 250, 'diff': -0.004, 'ci_low': -0.012, 'ci_high': 0.0, 'ci_includes_zero': True, 'family': 'retrieval', 'required_n': 58, 'minimum_detectable_effect': 0.15, 'power_basis': 'baseline_arm', 'p_value': 0.6175, 'confirmatory': True}

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

`promover_com_reservas`

Decisões possíveis (plano §17): promover, recalibrar, reduzir_claim, bloquear_expansao.
Uma média única nunca é o resultado final; ver `summary.json` por task type e split.
