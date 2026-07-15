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
        self.enabled, self._text_open, self._printed, self._secrets = (
            enabled,
            False,
            set(),
            {v for k, v in os.environ.items() if v and _SECRET_FIELD.search(k)},
        )

    def heading(self, label: str) -> None:
        if self.enabled:
            self._close()
            print(f"\n=== {label} ===")

    def block(self, label: str, value: Any) -> None:
        if self.enabled:
            self.heading(label)
            print("\n".join(f"  {x}" for x in self._text(value).splitlines() or [""]))

    def json(self, label: str, value: Any) -> None:
        if self.enabled:
            self.block(
                label, json.dumps(self._safe(value), indent=2, ensure_ascii=False, default=str)
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
            self.block(f"{label} saved message history", self._history(history) or "(empty)")
            self.block(f"{label} new model input", model_input)

    def subagent_handoff(self, material: str) -> None:
        self.block("Parent → executive-brief subagent handoff", material)

    async def event_stream_handler(self, _ctx: Any, events: AsyncIterable[Any]) -> None:
        async for e in events:
            if isinstance(e, FunctionToolCallEvent):
                self.json(f"Tool call: {e.part.tool_name}", e.part.args)
            elif isinstance(e, FunctionToolResultEvent):
                self.block(f"Tool result: {e.part.tool_name}", e.part.content)
            elif isinstance(e, ToolCallEvent):
                self.json(f"Tool call: {e.part.tool_name}", e.part.args)
            elif isinstance(e, ToolResultEvent):
                self.block(f"Tool result: {e.part.tool_name}", e.part.content)
            elif isinstance(e, PartStartEvent) and isinstance(e.part, TextPart):
                self._start(e.index, e.part.content)
            elif isinstance(e, PartDeltaEvent) and isinstance(e.delta, TextPartDelta):
                self._write(e.index, e.delta.content_delta)
            elif isinstance(e, PartEndEvent) and isinstance(e.part, TextPart):
                if e.index not in self._printed:
                    self._start(e.index, e.part.content)
                self._close()

    def _start(self, i: int, content: str) -> None:
        if self.enabled:
            if not self._text_open:
                self.heading("Streamed model text")
                self._text_open = True
                print("  ", end="", flush=True)
            self._write(i, content)

    def _write(self, i: int, content: str) -> None:
        if self.enabled and content:
            print(self._redact(content), end="", flush=True)
            self._printed.add(i)

    def _close(self) -> None:
        if self._text_open:
            print()
            self._text_open = False

    def _history(self, history: list[Any]) -> str:
        lines = []
        for message in history:
            for part in getattr(message, "parts", []):
                value = getattr(
                    part,
                    "content",
                    {
                        "tool": getattr(part, "tool_name", None),
                        "arguments": getattr(part, "args", None),
                    },
                )
                lines.append(
                    f"[{getattr(part, 'part_kind', type(part).__name__)}] {self._text(value)}"
                )
        return "\n".join(lines)

    def _text(self, v: Any) -> str:
        return self._redact(
            v
            if isinstance(v, str)
            else json.dumps(self._safe(v), indent=2, ensure_ascii=False, default=str)
        )

    def _safe(self, v: Any) -> Any:
        if is_dataclass(v):
            v = asdict(v)
        if isinstance(v, dict):
            return {
                k: "[REDACTED]" if _SECRET_FIELD.search(str(k)) else self._safe(x)
                for k, x in v.items()
            }
        if isinstance(v, (list, tuple)):
            return [self._safe(x) for x in v]
        return self._redact(v) if isinstance(v, str) else v

    def _redact(self, text: str) -> str:
        for secret in self._secrets:
            text = text.replace(secret, "[REDACTED]")
        return _SECRET_FIELD.sub(r"\1=[REDACTED]", text)
