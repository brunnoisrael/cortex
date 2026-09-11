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
    dynamic_report = run_ccb_on_store(store)  # empty store: every task has nothing to check
    assert set(fixture_report) == set(dynamic_report) == {
        "tasks_passed", "tasks_total", "tasks_skipped", "per_task",
        "false_memory_rate", "provenance_coverage",
    }
    for report in (fixture_report, dynamic_report):
        for task_result in report["per_task"].values():
            assert set(task_result) == {"pass", "false_memories", "skipped"}


def test_ccb_dynamic_skips_rather_than_vacuously_passes_on_empty_store(store):
    """Item 8 follow-up: an empty store used to score a false 8/8 on the
    dogfood path (every 'if not X' branch recorded check(..., True, "")).
    Tasks with no applicable entity must be skipped, not passed, so
    tasks_total/tasks_passed can't be read as a real quality signal when
    there is nothing yet to check."""
    report = run_ccb_on_store(store)
    assert report["tasks_total"] == 0
    assert report["tasks_passed"] == 0
    assert report["tasks_skipped"] == 8
    assert all(r["skipped"] and r["pass"] is None for r in report["per_task"].values())