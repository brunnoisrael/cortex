"""Testes unitários para o LLM Judge (cortex.benchmarks.llm_judge)."""
import json
import tempfile
from pathlib import Path

from cortex.benchmarks.llm_judge import (
    JudgeCase,
    JudgeVerdict,
    build_judge_cases,
    evaluate_judge_metrics,
    export_judge_inbox,
    generate_heuristic_verdicts,
    load_verdicts,
)


def test_judge_case_export_and_load():
    case = JudgeCase(
        case_id="case_1",
        task_type="exact_recall",
        query="Qual o commit?",
        gold_answer="c5f1bd1",
        accepted_answers=["c5f1bd1"],
        expected_abstention=False,
        gold_evidence=["sess:1"],
        retrieved_evidence_ids=["sess:1"],
        retrieved_evidence_texts=["[sess:1] commit c5f1bd1"],
        compiled_context="",
        abstained=False,
        missing_evidence=[],
    )
    with tempfile.TemporaryDirectory() as tmp:
        inbox_path = Path(tmp) / "inbox.json"
        export_judge_inbox([case], inbox_path)
        assert inbox_path.exists()

        verdicts_path = Path(tmp) / "verdicts.json"
        verdict = JudgeVerdict(
            case_id="case_1",
            answer_supported=True,
            relevance_ranking=["sess:1"],
            abstention_appropriate=True,
            fidelity_score=1.0,
            reasoning="Evidência contém o hash exato",
        )
        verdicts_path.write_text(
            json.dumps({"verdicts": [verdict.to_dict()]}),
            encoding="utf-8",
        )

        loaded = load_verdicts(verdicts_path)
        assert "case_1" in loaded
        assert loaded["case_1"].answer_supported is True
        assert loaded["case_1"].relevance_ranking == ["sess:1"]

        metrics = evaluate_judge_metrics([case], loaded)
        assert metrics["judge_answer_support_recall"] == 1.0
        assert metrics["judge_mrr"] == 1.0
        assert metrics["judge_abstention_accuracy"] == 1.0
