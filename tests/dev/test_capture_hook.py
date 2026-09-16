"""Testes para SessionCapture com IDs explícitos de evento."""
import json
import tempfile
from pathlib import Path

from cortex.dev.capture_hook import SessionCapture, create_capture


def test_capture_event_generates_explicit_ids():
    with tempfile.TemporaryDirectory() as tmp:
        capture = SessionCapture(output_dir=tmp, session_id="test_session")
        id0 = capture.capture_user_instruction("Iniciar sessão")
        id1 = capture.capture_assistant_response("Entendido, iniciando")
        id2 = capture.capture_tool_result("pytest", "5 passed")
        id3 = capture.capture_commit("a1b2c3d", "feat: initial commit", ["file1.py"])

        assert id0 == "test_session:0"
        assert id1 == "test_session:1"
        assert id2 == "test_session:2"
        assert id3 == "test_session:3"

        events = capture.current_session["events"]
        assert len(events) == 4
        assert [e["id"] for e in events] == [
            "test_session:0",
            "test_session:1",
            "test_session:2",
            "test_session:3",
        ]

        saved_path = capture.save_session()
        data = json.loads(saved_path.read_text(encoding="utf-8"))
        assert len(data["events"]) == 4
        for idx, ev in enumerate(data["events"]):
            assert ev["id"] == f"test_session:{idx}"


def test_capture_event_supports_custom_explicit_id():
    with tempfile.TemporaryDirectory() as tmp:
        capture = SessionCapture(output_dir=tmp, session_id="custom_sess")
        custom_id = "custom_sess:custom_42"
        res_id = capture.capture_event("user", "Hello", event_id=custom_id)
        assert res_id == custom_id
        assert capture.current_session["events"][0]["id"] == custom_id
