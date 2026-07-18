"""Tests for the terminal trace formatter; no model or network is required."""

import asyncio
import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from trace import LiveTrace
from unittest.mock import patch

from pydantic_ai.messages import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartStartEvent,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
)


class LiveTraceTests(unittest.TestCase):
    def test_trace_file_contains_redacted_tool_details(self) -> None:
        with patch.dict(os.environ, {"OPENAI_API_KEY": "expected-secret"}, clear=False):
            with tempfile.TemporaryDirectory() as directory:
                output = io.StringIO()
                with redirect_stdout(output):
                    trace = LiveTrace(True, log_dir=Path(directory))
                trace.json("Tool call: lookup", {"city": "Singapore", "api_key": "not-shown"})
                trace.block("Input", "key=expected-secret")
                trace.close()
                assert trace.log_path is not None
                rendered = trace.log_path.read_text(encoding="utf-8")

        self.assertRegex(trace.log_path.name, r"^trace_\d{8}-\d{6}_01_rag_in_context\.log$")
        self.assertIn('"city": "Singapore"', rendered)
        self.assertIn("[REDACTED]", rendered)
        self.assertNotIn("expected-secret", rendered)
        self.assertNotIn("not-shown", rendered)
        self.assertEqual(output.getvalue(), "")

    def test_tool_events_are_logged_but_not_printed(self) -> None:
        async def events():
            yield FunctionToolCallEvent(ToolCallPart("search_course_notes", {"question": "RAG"}))
            yield FunctionToolResultEvent(ToolReturnPart("search_course_notes", "Course passage"))

        with tempfile.TemporaryDirectory() as directory:
            output = io.StringIO()
            with redirect_stdout(output):
                trace = LiveTrace(True, log_dir=Path(directory))
                asyncio.run(trace.event_stream_handler(None, events()))
                trace.close()
            assert trace.log_path is not None
            rendered = trace.log_path.read_text(encoding="utf-8")

        self.assertIn("Tool call: search_course_notes", rendered)
        self.assertIn("Tool result: search_course_notes", rendered)
        self.assertIn("Course passage", rendered)
        self.assertEqual(output.getvalue(), "")

    def test_finished_response_is_the_only_terminal_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = io.StringIO()
            with redirect_stdout(output):
                trace = LiveTrace(True, log_dir=Path(directory))
                trace.subagent_handoff("Material for the specialist")
                trace.finish_response("Final answer")
                trace.close()
            assert trace.log_path is not None
            rendered = trace.log_path.read_text(encoding="utf-8")

        self.assertIn("Parent → executive-brief subagent handoff", rendered)
        self.assertEqual(output.getvalue(), "assistant> Final answer\n")

    def test_internal_agent_text_is_logged_but_not_printed(self) -> None:
        async def events():
            yield PartStartEvent(index=0, part=TextPart("Internal subagent text"))

        with tempfile.TemporaryDirectory() as directory:
            output = io.StringIO()
            with redirect_stdout(output):
                trace = LiveTrace(True, log_dir=Path(directory))
                asyncio.run(trace.log_event_stream_handler(None, events()))
                trace.finish_response("Parent answer")
                trace.close()
            assert trace.log_path is not None
            rendered = trace.log_path.read_text(encoding="utf-8")

        self.assertIn("Internal subagent text", rendered)
        self.assertEqual(output.getvalue(), "assistant> Parent answer\n")

    def test_disabled_trace_does_not_create_a_log(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trace = LiveTrace(False, log_dir=Path(directory))
            trace.block("Ignored", "value")
            trace.close()

        self.assertIsNone(trace.log_path)

    def test_subagent_handoff_has_its_own_label(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            trace = LiveTrace(True, log_dir=Path(directory))
            trace.subagent_handoff("Material for the specialist")
            trace.close()
            assert trace.log_path is not None
            rendered = trace.log_path.read_text(encoding="utf-8")

        self.assertIn("Parent → executive-brief subagent handoff", rendered)

    def test_numbered_turns_separate_user_messages_from_model_input(self) -> None:
        history = [
            SimpleNamespace(
                parts=[SimpleNamespace(part_kind="user-prompt", content="First question")]
            )
        ]

        with tempfile.TemporaryDirectory() as directory:
            with redirect_stdout(io.StringIO()):
                trace = LiveTrace(True, log_dir=Path(directory))
                trace.begin_turn(
                    "System instructions", [], "Expanded first prompt", user_input="First question"
                )
                trace.finish_response("First answer")
                trace.begin_turn("System instructions", history, "Follow-up question")
                trace.finish_response("Follow-up answer")
                trace.close()
            assert trace.log_path is not None
            rendered = trace.log_path.read_text(encoding="utf-8")

        self.assertIn("=== Conversation Turn 1 ===", rendered)
        self.assertIn("=== Conversation Turn 2 ===", rendered)
        self.assertIn("=== Conversation Turn 1 — User ===", rendered)
        self.assertIn("Message entered in terminal:", rendered)
        self.assertIn("First question", rendered)
        self.assertIn("Expanded first prompt", rendered)
        self.assertNotIn("Saved history passed to the model", rendered)
        self.assertNotIn("Instructions sent to the model", rendered)
        self.assertNotIn("End of Conversation Turn", rendered)

    def test_internal_agent_runs_stay_within_the_parent_turn(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with redirect_stdout(io.StringIO()):
                trace = LiveTrace(True, log_dir=Path(directory))
                trace.begin_turn("Parent instructions", [], "Question", label="Parent agent")
                trace.begin_turn(
                    "Subagent instructions",
                    [],
                    "Material",
                    label="Executive-brief subagent",
                    conversation_turn=False,
                )
                trace.resume_conversation_turn("Parent agent")
                trace.finish_response("Answer")
                trace.close()
            assert trace.log_path is not None
            rendered = trace.log_path.read_text(encoding="utf-8")

        self.assertIn("Conversation Turn 1 — Internal Executive-brief subagent", rendered)
        self.assertIn("Conversation Turn 1 — Parent agent resumes", rendered)
        self.assertNotIn("Conversation Turn 2", rendered)


if __name__ == "__main__":
    unittest.main()
