"""Part 3 assistant: model-selected RAG plus a local MCP weather tool."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from trace import LiveTrace

from fastmcp.client.transports import StdioTransport
from pydantic_ai import Agent as PydanticAgent
from pydantic_ai import RunContext
from pydantic_ai.mcp import MCPToolset
from rag import format_context, open_collection, retrieve

SYSTEM_PROMPT = """You are a helpful course assistant. Use search_course_notes for
course, RAG, or Pydantic AI questions, and use the weather tool for current weather
questions. Do not use tools for ordinary general knowledge. Mention used sources or tools."""
WEATHER_SERVER_PATH = Path(__file__).with_name("weather_server.py")


@dataclass
class ToolDependencies:
    """Runtime data made available to local Python function tools."""

    collection: object
    diagnostics: list[str] = field(default_factory=list)


class CourseAssistant:
    """Owns prompt, session memory, function tools, and the MCP toolset lifecycle."""

    def __init__(self, model_name: str, trace: bool = False) -> None:
        self.model_name = model_name
        self.dependencies = ToolDependencies(collection=open_collection())
        self.message_history = []  # Pydantic AI messages retained for this CLI session.
        transport = StdioTransport(command=sys.executable, args=[str(WEATHER_SERVER_PATH)])
        self.weather_toolset = MCPToolset(transport)
        self.agent: PydanticAgent[ToolDependencies, str] | None = None
        self.trace = LiveTrace(trace)

    @property
    def diagnostics(self) -> list[str]:
        """Return local function-tool activity from the most recent turn."""
        return self.dependencies.diagnostics

    async def __aenter__(self) -> "CourseAssistant":
        await self.weather_toolset.__aenter__()
        self.agent = self._build_agent()
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.weather_toolset.__aexit__(*exc_info)

    def _build_agent(self) -> PydanticAgent[ToolDependencies, str]:
        """Create the agent and register its Python and MCP tools."""
        agent = PydanticAgent(
            self.model_name,
            deps_type=ToolDependencies,
            instructions=SYSTEM_PROMPT,
            toolsets=[self.weather_toolset],
        )

        @agent.tool
        def search_course_notes(ctx: RunContext[ToolDependencies], question: str) -> str:
            """Search local course notes for relevant source passages."""
            hits = retrieve(ctx.deps.collection, question)
            sources = ", ".join(hit["source"] for hit in hits)
            ctx.deps.diagnostics.append(f"[tool] search_course_notes: {sources}")
            return format_context(hits)

        return agent

    async def ask(self, question: str) -> str:
        """Give the model a turn; it can select either local or MCP tools."""
        if self.agent is None:
            raise RuntimeError("Use 'async with CourseAssistant(...)' before asking questions.")

        self.dependencies.diagnostics.clear()
        self.trace.begin_turn(SYSTEM_PROMPT, self.message_history, question)
        result = await self.agent.run(
            question,
            deps=self.dependencies,
            message_history=self.message_history,
            event_stream_handler=self.trace.event_stream_handler if self.trace.enabled else None,
        )
        self.message_history = result.all_messages()
        return result.output
