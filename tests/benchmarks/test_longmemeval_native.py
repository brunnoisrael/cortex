"""Native LongMemEval loader + session-grain retrieval scoring."""

from __future__ import annotations

import json
from pathlib import Path

from cortex.benchmarks.adapters.base import AdapterResult
from cortex.benchmarks.loaders.longmemeval_native import normalize_longmemeval
from cortex.benchmarks.metrics import case_metrics
from cortex.benchmarks.reports import write_reports


def _cleaned_row() -> dict:
    return {
        "question_id": "abc123",
        "question_type": "single-session-user",
        "question": "What degree did I graduate with?",
        "question_date": "2023/05/20 (Sat) 02:21",
        "answer": "Business Administration",
        "answer_session_ids": ["answer_sess"],
        "haystack_session_ids": ["noise_sess", "answer_sess"],
        "haystack_dates": ["2023/05/18 (Thu) 10:00", "2023/05/19 (Fri) 11:00"],
        "haystack_sessions": [
            [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"}],
            [
                {"role": "user", "content": "I graduated with Business Administration"},
                {"role": "assistant", "content": "noted"},
            ],
        ],
    }


def test_native_loader_keeps_session_gold_and_nl_answer(tmp_path: Path):
    path = tmp_path / "longmemeval_s_cleaned.json"
    path.write_text(json.dumps([_cleaned_row()]), encoding="utf-8")
    instance = normalize_longmemeval(path)[0]
    assert instance.source == "longmemeval"
    assert instance.gold.annotation_quality == "exploratory"
    assert instance.gold.answer == "Business Administration"
    assert instance.gold.gold_evidence == ["answer_sess"]
    assert instance.gold.current_entities == ["answer_sess"]
    assert instance.metadata["evidence_grain"] == "session"
    assert instance.metadata["external_control"] is True
    assert instance.task_type == "exact_recall"
    # Cutoff is the synthetic last session; haystack is fully visible.
    assert instance.cutoff.session_index == 2
    assert [s.session_id for s in instance.history_until_cutoff()] == ["noise_sess", "answer_sess"]


def test_session_grain_recall_hits_when_an_event_from_the_gold_session_is_retrieved(tmp_path: Path):
    path = tmp_path / "longmemeval_s_cleaned.json"
    path.write_text(json.dumps([_cleaned_row()]), encoding="utf-8")
    instance = normalize_longmemeval(path)[0]
    hit = AdapterResult(
        case_id=instance.id, adapter="bm25",
        retrieved=["answer_sess:0", "noise_sess:1"],
        selected=["answer_sess:0"],
        evidence=["answer_sess:0"],
        trace={"extracted_ids": ["noise_sess:0", "answer_sess:1"]},
    )
    miss = AdapterResult(
        case_id=instance.id, adapter="bm25",
        retrieved=["noise_sess:0"], selected=["noise_sess:0"], evidence=["noise_sess:0"],
        trace={"extracted_ids": ["noise_sess:0"]},
    )
    assert case_metrics(hit, instance)["recall_at_k"] == 1.0
    assert case_metrics(hit, instance)["extraction_recall"] == 1.0
    assert case_metrics(miss, instance)["recall_at_k"] == 0.0
    assert case_metrics(miss, instance)["extraction_recall"] == 0.0


def test_exploratory_run_cannot_promote(tmp_path: Path):
    rows = [
        {"case_id": "c1", "adapter": "cortex", "metric": "stale_leak_rate", "value": 0.0,
         "task_type": "exact_recall", "split": "dev", "annotation_quality": "exploratory"},
        {"case_id": "c1", "adapter": "bm25", "metric": "stale_leak_rate", "value": 1.0,
         "task_type": "exact_recall", "split": "dev", "annotation_quality": "exploratory"},
        {"case_id": "c1", "adapter": "cortex", "metric": "recall_at_k", "value": 1.0,
         "task_type": "exact_recall", "split": "dev", "annotation_quality": "exploratory"},
        {"case_id": "c1", "adapter": "bm25", "metric": "recall_at_k", "value": 0.0,
         "task_type": "exact_recall", "split": "dev", "annotation_quality": "exploratory"},
        {"case_id": "c2", "adapter": "cortex", "metric": "stale_leak_rate", "value": 0.0,
         "task_type": "exact_recall", "split": "dev", "annotation_quality": "exploratory"},
        {"case_id": "c2", "adapter": "bm25", "metric": "stale_leak_rate", "value": 1.0,
         "task_type": "exact_recall", "split": "dev", "annotation_quality": "exploratory"},
        {"case_id": "c2", "adapter": "cortex", "metric": "recall_at_k", "value": 1.0,
         "task_type": "exact_recall", "split": "dev", "annotation_quality": "exploratory"},
        {"case_id": "c2", "adapter": "bm25", "metric": "recall_at_k", "value": 0.0,
         "task_type": "exact_recall", "split": "dev", "annotation_quality": "exploratory"},
    ]
    out = tmp_path / "report"
    write_reports(out, {"cortex_version": "0.1.0", "corpus_hash": "sha256:" + "0" * 64,
                        "dataset_revisions": {"longmemeval": "test"}}, rows, [], [])
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["claim_class"] == "exploratory"
    assert summary["decision"] == "diagnostico"
    assert summary["endpoints"]["cortex"]["recall_at_k"]["confirmatory"] is False
