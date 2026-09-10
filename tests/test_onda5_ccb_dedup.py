"""Regression test for PLANO_ENDURECIMENTO_2026-09-08.md item 5.4:
ccb.py's fixture evaluator (_evaluate) and dogfooding evaluator
(_evaluate_dynamic) had ~100 near-identical lines (leak-counting closure +
final scoring block) copy-pasted between them. Both now call the same
_leak_count/_make_check/_score helpers; this pins the previously-untested
fixture result (test_super_evolucao.py only asserted tasks_passed > 0) and
the shared report shape both evaluators must produce."""

from __future__ import annotations

from cortex.benchmarks.ccb import run_ccb, run_ccb_on_store


def test_ccb_fixture_passes_all_eight_tasks_after_dedup():
    report = run_ccb()
    assert report["tasks_total"] == 8
    assert report["tasks_passed"] == 8, report["per_task"]
    assert report["false_memory_rate"] == 0.0
    assert report["provenance_coverage"] == 1.0


def test_ccb_fixture_and_dynamic_reports_share_the_same_shape(store):
    fixture_report = run_ccb()
    dynamic_report = run_ccb_on_store(store)  # empty store: every task no-ops to pass=True
    assert set(fixture_report) == set(dynamic_report) == {
        "tasks_passed", "tasks_total", "per_task", "false_memory_rate", "provenance_coverage",
    }
    for report in (fixture_report, dynamic_report):
        for task_result in report["per_task"].values():
            assert set(task_result) == {"pass", "false_memories"}
