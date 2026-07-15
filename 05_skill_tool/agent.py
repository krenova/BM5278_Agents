"""Part 5 assistant: MCP tools plus a Markdown-backed summary skill."""

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
from skill_loader import load_skill

SYSTEM_PROMPT = """You are a helpful course assistant. Use search_course_notes for
course questions and the weather tool for current weather. For an executive brief or
summary, call load_executive_brief_skill, then follow its instructions yourself.
Mention tool use."""
WEATHER_SERVER_PATH = Path(__file__).with_name("weather_server.py")
SKILL_PATH = Path(__file__).with_name("SKILL.md")


@dataclass
class ToolDependencies:
    """Runtime data made available to local function tools."""

    collection: object
    diagnostics: list[str] = field(default_factory=list)


class CourseAssistant:
    """Owns prompt, memory, function tools, MCP lifecycle, and skill loading."""

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
        """Return local tool and skill activity from the most recent turn."""
        return self.dependencies.diagnostics

    async def __aenter__(self) -> "CourseAssistant":
        await self.weather_toolset.__aenter__()
        self.agent = self._build_agent()
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.weather_toolset.__aexit__(*exc_info)

    def _build_agent(self) -> PydanticAgent[ToolDependencies, str]:
        """Create the agent and register retrieval and Markdown-skill tools."""
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
            ctx.deps.diagnostics.append("[tool] search_course_notes")
            return format_context(hits)

        @agent.tool
        def load_executive_brief_skill(ctx: RunContext[ToolDependencies]) -> str:
            """Load Markdown instructions for executive-brief summaries."""
            ctx.deps.diagnostics.append("[skill] loaded SKILL.md")
            skill = load_skill(SKILL_PATH)
            self.trace.block("Loaded executive-brief skill (SKILL.md)", skill)
            return skill

        return agent

    async def ask(self, question: str) -> str:
        """Give the model a turn and retain its result as conversation memory."""
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
