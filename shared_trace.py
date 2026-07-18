"""Credential-safe file tracing with conversation-only terminal output."""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterable, TextIO

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

# Matches a credential-like field name on its own, e.g. as a dict key or embedded in
# an env var name like OPENAI_API_KEY (no \b: "_" is a word char, so a boundary would
# not exist between "OPENAI_" and "API_KEY").
_SECRET_FIELD = re.compile(r"(api[ _-]?key|token|secret|password|credential|authorization)", re.I)
# Matches only an actual `field = value` / `field: value` assignment, so prose that
# merely contains one of these words (e.g. "a secret base", "acted secretly") is left
# alone; only genuine key/value leaks like "api_key=sk-..." get redacted.
_SECRET_ASSIGNMENT = re.compile(
    r"(api[ _-]?key|token|secret|password|credential|authorization)(\s*[:=]\s*)(\S+)",
    re.I,
)
_BANNER_WIDTH = 88


def describe_local_toolset(toolset: Any) -> list[dict[str, Any]]:
    """List a local FunctionToolset's tools with their full JSON parameter schema.

    This is exactly the (name, description, schema) triple pydantic_ai sends the
    model on every turn — no network call is involved, so it can run synchronously.
    """
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.function_schema.json_schema,
        }
        for tool in toolset.tools.values()
    ]


async def describe_mcp_toolset(toolset: Any) -> list[dict[str, Any]]:
    """List a remote MCP toolset's tools as name + description only (no schema).

    Calls the same `list_tools()` pydantic_ai issues automatically on every
    `agent.run()` (and caches after the first call). Schemas are omitted here
    because a real gateway can expose dozens of unrelated tools with large
    schemas; see the tool's own `inputSchema` if you need the full picture.
    """
    mcp_tools = await toolset.list_tools()
    return [{"name": tool.name, "description": tool.description} for tool in mcp_tools]


class LiveTrace:
    """Save observable agent exchanges while streaming only the final reply to stdout."""

    def __init__(
        self,
        enabled: bool = False,
        log_dir: Path | None = None,
        *,
        tutorial_dir: Path | None = None,
    ) -> None:
        self.enabled = enabled
        self._tutorial_dir = tutorial_dir or Path(__file__).resolve().parent
        self.log_path: Path | None = None
        self._log: TextIO | None = None
        self._log_text_open = False
        self._terminal_text_open = False
        self._terminal_had_text = False
        self._conversation_turn = 0
        self._active_run_label: str | None = None
        self._secrets = {
            value for key, value in os.environ.items() if value and _SECRET_FIELD.search(key)
        }
        if self.enabled:
            self._open_log(log_dir or self._tutorial_dir / "logs")

    def _open_log(self, log_dir: Path) -> None:
        log_dir.mkdir(parents=True, exist_ok=True)
        tutorial = self._tutorial_dir.name
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        candidate = log_dir / f"trace_{timestamp}_{tutorial}.log"
        suffix = 1
        while candidate.exists():
            candidate = log_dir / f"trace_{timestamp}_{tutorial}_{suffix}.log"
            suffix += 1
        self.log_path = candidate
        self._log = candidate.open("x", encoding="utf-8", buffering=1)
        self.banner("Trace session")
        self._write_log(
            f"  Tutorial: {tutorial}\n  Started: {datetime.now().astimezone().isoformat()}\n"
        )

    def close(self) -> None:
        """Flush and close the current session log, if tracing is enabled."""
        self._close_log_text()
        if self._log is not None:
            self._log.close()
            self._log = None

    def heading(self, label: str) -> None:
        if self.enabled:
            self._close_log_text()
            self._write_log(f"\n=== {label} ===\n")

    def banner(self, label: str) -> None:
        """Log a 3-line banner, used to make session start and new turns obvious."""
        if self.enabled:
            self._close_log_text()
            bar = "=" * _BANNER_WIDTH
            middle = f"=== {label} ".ljust(_BANNER_WIDTH, "=")
            self._write_log(f"\n{bar}\n{middle}\n{bar}\n")

    def log_system_prompt(self, instructions: str) -> None:
        """Log the system prompt once at startup; it is resent unchanged on every turn."""
        self.block("Startup — System prompt sent to the model with every turn", instructions)

    def block(self, label: str, value: Any) -> None:
        if self.enabled:
            self.heading(label)
            text = self._redact(self._to_text(value))
            self._write_log("\n".join(f"  {line}" for line in text.splitlines() or [""]) + "\n")

    def json(self, label: str, value: Any) -> None:
        if self.enabled:
            self.block(
                label, json.dumps(self._sanitize(value), indent=2, ensure_ascii=False, default=str)
            )

    def begin_turn(
        self,
        instructions: str,
        model_input: str,
        *,
        label: str = "Agent",
        conversation_turn: bool = True,
        user_input: str | None = None,
    ) -> None:
        if not self.enabled:
            return
        if conversation_turn:
            self._conversation_turn += 1
            self._active_run_label = f"Conversation Turn {self._conversation_turn} — {label}"
            self.banner(f"Conversation Turn {self._conversation_turn}")
        else:
            self._active_run_label = (
                f"Conversation Turn {self._conversation_turn} — Internal {label}"
            )
            self.heading(self._active_run_label)
            # This internal run uses its own prompt (e.g. a subagent), distinct
            # from the parent conversation's prompt already logged at startup.
            self.block(f"{self._active_run_label} — System prompt sent to the model", instructions)
        if user_input is not None:
            self.block(
                f"Conversation Turn {self._conversation_turn} — User",
                f"Message entered in terminal:\n{user_input}",
            )
        self.block(f"{self._active_run_label} — New input sent to the model", model_input)

    def resume_conversation_turn(self, label: str) -> None:
        """Associate subsequent events with the parent conversation after internal work."""
        if not self.enabled:
            return
        self._active_run_label = f"Conversation Turn {self._conversation_turn} — {label}"
        self.heading(f"{self._active_run_label} resumes")

    def subagent_handoff(self, material: str) -> None:
        self.block(
            f"Conversation Turn {self._conversation_turn}"
            " — Parent → executive-brief subagent handoff",
            material,
        )

    async def event_stream_handler(self, _: Any, events: AsyncIterable[Any]) -> None:
        """Log events and stream the user-facing agent's text to the terminal."""
        await self._handle_events(events, show_terminal=True)

    async def log_event_stream_handler(self, _: Any, events: AsyncIterable[Any]) -> None:
        """Log events without exposing an internal agent's text in the terminal."""
        await self._handle_events(events, show_terminal=False)

    async def _handle_events(self, events: AsyncIterable[Any], *, show_terminal: bool) -> None:
        printed_text_indices: set[int] = set()
        async for event in events:
            if isinstance(event, FunctionToolCallEvent):
                self.json(self._event_label(f"Tool call: {event.part.tool_name}"), event.part.args)
            elif isinstance(event, FunctionToolResultEvent):
                self.block(
                    self._event_label(f"Tool result: {event.part.tool_name}"), event.part.content
                )
            elif isinstance(event, ToolCallEvent):
                self.json(self._event_label(f"Tool call: {event.part.tool_name}"), event.part.args)
            elif isinstance(event, ToolResultEvent):
                self.block(
                    self._event_label(f"Tool result: {event.part.tool_name}"), event.part.content
                )
            elif isinstance(event, PartStartEvent) and isinstance(event.part, TextPart):
                self._write_model_text(event.part.content, show_terminal)
                printed_text_indices.add(event.index)
            elif isinstance(event, PartDeltaEvent) and isinstance(event.delta, TextPartDelta):
                self._write_model_text(event.delta.content_delta, show_terminal)
                printed_text_indices.add(event.index)
            elif isinstance(event, PartEndEvent) and isinstance(event.part, TextPart):
                if event.index not in printed_text_indices:
                    self._write_model_text(event.part.content, show_terminal)

    def finish_response(self, response: str) -> None:
        """End the terminal response, falling back to the completed output if needed."""
        if not self.enabled:
            return
        if self._terminal_text_open:
            print()
        elif not self._terminal_had_text:
            print(f"assistant> {self._redact(response)}")
        self._terminal_text_open = False
        self._terminal_had_text = False

    def _write_model_text(self, content: str, show_terminal: bool) -> None:
        if not self.enabled or not content:
            return
        if not self._log_text_open:
            self.heading(self._event_label("Streamed model text"))
            self._log_text_open = True
            self._write_log("  ")
        safe_content = self._redact(content)
        self._write_log(safe_content)
        if show_terminal:
            if not self._terminal_text_open:
                print("assistant> ", end="", flush=True)
                self._terminal_text_open = True
            print(safe_content, end="", flush=True)
            self._terminal_had_text = True

    def _close_log_text(self) -> None:
        if self._log_text_open:
            self._write_log("\n")
            self._log_text_open = False

    def _write_log(self, text: str) -> None:
        if self._log is not None:
            self._log.write(text)
            self._log.flush()

    def _event_label(self, event: str) -> str:
        return f"{self._active_run_label or 'Agent'} — {event}"

    def _to_text(self, value: Any) -> str:
        if isinstance(value, str):
            return value
        return json.dumps(self._sanitize(value), indent=2, ensure_ascii=False, default=str)

    def _sanitize(self, value: Any) -> Any:
        if is_dataclass(value):
            value = asdict(value)
        if isinstance(value, dict):
            return {
                key: "[REDACTED]" if _SECRET_FIELD.search(str(key)) else self._sanitize(item)
                for key, item in value.items()
            }
        if isinstance(value, (list, tuple)):
            return [self._sanitize(item) for item in value]
        if isinstance(value, str):
            return self._redact(value)
        return value

    def _redact(self, text: str) -> str:
        for secret in self._secrets:
            text = text.replace(secret, "[REDACTED]")
        return _SECRET_ASSIGNMENT.sub(r"\1\2[REDACTED]", text)
