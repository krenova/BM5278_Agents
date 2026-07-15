"""Part 4 assistant: MCP tools plus an executive-brief subagent."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from trace import LiveTrace
from typing import Any

from fastmcp.client.transports import StdioTransport
from pydantic_ai import Agent as PydanticAgent
from pydantic_ai import RunContext
from pydantic_ai.mcp import MCPToolset
from rag import format_context, open_collection, retrieve

PARENT_PROMPT = """You are a helpful course assistant. Use search_course_notes for
course questions and the weather tool for current weather. For an executive brief or
summary, call create_executive_brief. Mention tool use."""
BRIEF_PROMPT = """Create an executive brief using exactly these Markdown headings:
## Key points, ## Risks, ## Recommended actions. Be concise and preserve uncertainty."""
WEATHER_SERVER_PATH = Path(__file__).with_name("weather_server.py")


@dataclass
class ToolDependencies:
    """Runtime data shared by the parent agent and its tools."""

    collection: object
    diagnostics: list[str] = field(default_factory=list)
    usage: Any | None = None


class CourseAssistant:
    """Owns parent memory, tools, MCP lifecycle, and the brief subagent."""

    def __init__(self, model_name: str, trace: bool = False) -> None:
        self.model_name = model_name
        self.dependencies = ToolDependencies(collection=open_collection())
        self.message_history = []  # Parent-agent messages retained for this CLI session.
        transport = StdioTransport(command=sys.executable, args=[str(WEATHER_SERVER_PATH)])
        self.weather_toolset = MCPToolset(transport)
        self.parent_agent: PydanticAgent[ToolDependencies, str] | None = None
        self.brief_agent = PydanticAgent(model_name, instructions=BRIEF_PROMPT)
        self.trace = LiveTrace(trace)

    @property
    def diagnostics(self) -> list[str]:
        """Return local tool and subagent activity from the most recent turn."""
        return self.dependencies.diagnostics

    async def __aenter__(self) -> "CourseAssistant":
        await self.weather_toolset.__aenter__()
        self.parent_agent = self._build_parent_agent()
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.weather_toolset.__aexit__(*exc_info)

    def _build_parent_agent(self) -> PydanticAgent[ToolDependencies, str]:
        """Create the parent and register retrieval and subagent-delegation tools."""
        agent = PydanticAgent(
            self.model_name,
            deps_type=ToolDependencies,
            instructions=PARENT_PROMPT,
            toolsets=[self.weather_toolset],
        )

        @agent.tool
        def search_course_notes(ctx: RunContext[ToolDependencies], question: str) -> str:
            """Search local course notes for relevant source passages."""
            hits = retrieve(ctx.deps.collection, question)
            ctx.deps.diagnostics.append("[tool] search_course_notes")
            return format_context(hits)

        @agent.tool
        async def create_executive_brief(ctx: RunContext[ToolDependencies], material: str) -> str:
            """Delegate material to a specialist that creates an executive brief."""
            ctx.deps.diagnostics.append("[subagent] executive brief")
            self.trace.subagent_handoff(material)
            self.trace.begin_turn(BRIEF_PROMPT, [], material, label="Executive-brief subagent")
            result = await self.brief_agent.run(
                material,
                usage=ctx.deps.usage,
                event_stream_handler=self.trace.event_stream_handler
                if self.trace.enabled
                else None,
            )
            ctx.deps.usage = result.usage()
            return result.output

        return agent

    async def ask(self, question: str) -> str:
        """Run the parent tool loop and retain its output as conversation memory."""
        if self.parent_agent is None:
            raise RuntimeError("Use 'async with CourseAssistant(...)' before asking questions.")

        self.dependencies.diagnostics.clear()
        self.trace.begin_turn(PARENT_PROMPT, self.message_history, question, label="Parent agent")
        result = await self.parent_agent.run(
            question,
            deps=self.dependencies,
            message_history=self.message_history,
            usage=self.dependencies.usage,
            event_stream_handler=self.trace.event_stream_handler if self.trace.enabled else None,
        )
        self.dependencies.usage = result.usage()
        self.message_history = result.all_messages()
        return result.output
