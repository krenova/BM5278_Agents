"""Terminal-only, credential-safe tracing for the lesson agents."""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, is_dataclass
from typing import Any, AsyncIterable

from pydantic_ai.messages import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartEndEvent,
    PartStartEvent,
    TextPart,
    TextPartDelta,
    ToolCallEvent,
    ToolResultEvent,
)

_SECRET_FIELD = re.compile(r"(api[ _-]?key|token|secret|password|credential|authorization)", re.I)


class LiveTrace:
    """Print observable model messages and tool exchanges, never hidden reasoning."""

    def __init__(self, enabled: bool = False) -> None:
        self.enabled, self._text_open, self._printed_text_indices = enabled, False, set()
        self._secrets = {v for k, v in os.environ.items() if v and _SECRET_FIELD.search(k)}

    def heading(self, label: str) -> None:
        if self.enabled:
            self._close_text()
            print(f"\n=== {label} ===")

    def block(self, label: str, value: Any) -> None:
        if self.enabled:
            self.heading(label)
            text = self._redact(self._to_text(value))
            print("\n".join(f"  {line}" for line in text.splitlines() or [""]))

    def json(self, label: str, value: Any) -> None:
        if self.enabled:
            self.heading(label)
            print(
                "\n".join(
                    f"  {line}"
                    for line in json.dumps(
                        self._sanitize(value), indent=2, ensure_ascii=False, default=str
                    ).splitlines()
                )
            )

    def begin_turn(
        self, instructions: str, history: list[Any], model_input: str, *, label: str = "Agent"
    ) -> None:
        if self.enabled:
            self.heading(f"{label} trace")
            print(
                "  This trace shows observable agent messages and tool exchanges, "
                "not hidden model reasoning."
            )
            self.block(f"{label} instructions", instructions)
            self.block(f"{label} saved message history", self._render_history(history) or "(empty)")
            self.block(f"{label} new model input", model_input)

    def subagent_handoff(self, material: str) -> None:
        self.block("Parent → executive-brief subagent handoff", material)

    async def event_stream_handler(self, _ctx: Any, events: AsyncIterable[Any]) -> None:
        async for event in events:
            if isinstance(event, FunctionToolCallEvent):
                self.json(f"Tool call: {event.part.tool_name}", event.part.args)
            elif isinstance(event, FunctionToolResultEvent):
                self.block(f"Tool result: {event.part.tool_name}", event.part.content)
            elif isinstance(event, ToolCallEvent):
                self.json(f"Tool call: {event.part.tool_name}", event.part.args)
            elif isinstance(event, ToolResultEvent):
                self.block(f"Tool result: {event.part.tool_name}", event.part.content)
            elif isinstance(event, PartStartEvent) and isinstance(event.part, TextPart):
                self._start_text(event.index, event.part.content)
            elif isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
                self._write_text(event.index, event.delta.content_delta)
            elif isinstance(event, PartEndEvent) and isinstance(event.part, TextPart):
                if event.index not in self._printed_text_indices:
                    self._start_text(event.index, event.part.content)
                self._close_text()

    def _start_text(self, index: int, content: str) -> None:
        if self.enabled:
            if not self._text_open:
                self.heading("Streamed model text")
                self._text_open = True
                print("  ", end="", flush=True)
            self._write_text(index, content)

    def _write_text(self, index: int, content: str) -> None:
        if self.enabled and content:
            print(self._redact(content), end="", flush=True)
            self._printed_text_indices.add(index)

    def _close_text(self) -> None:
        if self._text_open:
            print()
            self._text_open = False

    def _render_history(self, history: list[Any]) -> str:
        result = []
        for message in history:
            for part in getattr(message, "parts", []):
                kind = getattr(part, "part_kind", type(part).__name__)
                value = (
                    {"tool": part.tool_name, "arguments": part.args}
                    if hasattr(part, "tool_name") and hasattr(part, "args")
                    else {"tool": part.tool_name, "result": part.content}
                    if hasattr(part, "tool_name") and hasattr(part, "content")
                    else getattr(part, "content", str(part))
                )
                result.append(f"[{kind}] {self._to_text(value)}")
        return "\n".join(result)

    def _to_text(self, value: Any) -> str:
        return (
            value
            if isinstance(value, str)
            else json.dumps(self._sanitize(value), indent=2, ensure_ascii=False, default=str)
        )

    def _sanitize(self, value: Any) -> Any:
        if is_dataclass(value):
            value = asdict(value)
        if isinstance(value, dict):
            return {
                k: "[REDACTED]" if _SECRET_FIELD.search(str(k)) else self._sanitize(v)
                for k, v in value.items()
            }
        if isinstance(value, (list, tuple)):
            return [self._sanitize(v) for v in value]
        return self._redact(value) if isinstance(value, str) else value

    def _redact(self, text: str) -> str:
        for secret in self._secrets:
            text = text.replace(secret, "[REDACTED]")
        return _SECRET_FIELD.sub(r"\1=[REDACTED]", text)
