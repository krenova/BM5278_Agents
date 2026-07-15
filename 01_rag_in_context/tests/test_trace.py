"""Tests for the terminal trace formatter; no model or network is required."""

import asyncio
import io
import os
import unittest
from contextlib import redirect_stdout
from trace import LiveTrace
from unittest.mock import patch

from pydantic_ai.messages import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    ToolCallPart,
    ToolReturnPart,
)


class LiveTraceTests(unittest.TestCase):
    def test_pretty_json_and_configured_secret_redaction(self) -> None:
        with patch.dict(os.environ, {"OPENAI_API_KEY": "expected-secret"}, clear=False):
            output = io.StringIO()
            with redirect_stdout(output):
                trace = LiveTrace(True)
                trace.json("Tool call: lookup", {"city": "Singapore", "api_key": "not-shown"})
                trace.block("Input", "key=expected-secret")

        rendered = output.getvalue()
        self.assertIn('"city": "Singapore"', rendered)
        self.assertIn("[REDACTED]", rendered)
        self.assertNotIn("expected-secret", rendered)
        self.assertNotIn("not-shown", rendered)

    def test_function_call_and_result_labels(self) -> None:
        async def events():
            yield FunctionToolCallEvent(ToolCallPart("search_course_notes", {"question": "RAG"}))
            yield FunctionToolResultEvent(ToolReturnPart("search_course_notes", "Course passage"))

        output = io.StringIO()
        with redirect_stdout(output):
            asyncio.run(LiveTrace(True).event_stream_handler(None, events()))

        rendered = output.getvalue()
        self.assertIn("Tool call: search_course_notes", rendered)
        self.assertIn("Tool result: search_course_notes", rendered)
        self.assertIn("Course passage", rendered)

    def test_subagent_handoff_has_its_own_label(self) -> None:
        output = io.StringIO()
        with redirect_stdout(output):
            LiveTrace(True).subagent_handoff("Material for the specialist")

        self.assertIn("Parent → executive-brief subagent handoff", output.getvalue())


if __name__ == "__main__":
    unittest.main()
