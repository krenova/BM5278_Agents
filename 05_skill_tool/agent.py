"""Part 5 assistant: Star Wars MCP tools plus a Markdown-backed summary skill."""

from pathlib import Path
from trace import LiveTrace, describe_local_toolset, describe_mcp_toolset

from pydantic_ai import Agent as PydanticAgent
from pydantic_ai import FunctionToolset
from pydantic_ai.mcp import MCPToolset, StreamableHttpTransport
from rag import format_context, open_collection, retrieve
from skill_loader import load_skill

SYSTEM_PROMPT = """You are a helpful course assistant. Use search_course_notes for
course questions and Star Wars tools for questions about characters, planets,
starships, or films. For an executive brief or summary, call
load_executive_brief_skill, then follow its instructions yourself. Mention tool use."""
STAR_WARS_MCP_URL = "https://gateway.pipeworx.io/swapi/mcp"
# The gateway is a shared multi-domain router that bundles in ~20 unrelated tools
# (SEC filings, prediction markets, drug data, ...) alongside these four; keep the
# model's tool list scoped to what this lesson is actually about.
STAR_WARS_TOOL_NAMES = {"search_people", "get_planet", "get_starship", "get_film"}
SKILL_PATH = Path(__file__).with_name("SKILL.md")


class CourseAssistant:
    """Owns the Part 3 state plus a Yoda-voiced, Markdown-backed skill tool."""

    def __init__(self, model_name: str, trace: bool = False) -> None:
        self.collection = open_collection()  # Chroma collection for course-note retrieval.
        self.message_history = []  # Pydantic AI messages retained for this CLI session.
        self.diagnostics: list[str] = []  # Local-tool diagnostics shown when tracing is off.
        self.trace = LiveTrace(trace)

        self.course_note_toolset = FunctionToolset()

        @self.course_note_toolset.tool_plain
        def search_course_notes(question: str) -> str:
            """Search local course notes for relevant source passages."""
            hits = retrieve(self.collection, question)
            sources = ", ".join(hit["source"] for hit in hits)
            self.diagnostics.append(f"[tool] search_course_notes: {sources}")
            return format_context(hits)

        # This remote MCP toolset must be opened asynchronously before use.
        self.star_wars_mcp = MCPToolset(StreamableHttpTransport(STAR_WARS_MCP_URL))
        # Filtering is applied as a wrapper: the model only ever sees the four
        # tools below, even though the gateway itself exposes many more.
        self.star_wars_toolset = self.star_wars_mcp.filtered(
            lambda ctx, tool_def: tool_def.name in STAR_WARS_TOOL_NAMES
        )

        # A separate toolset for the single skill-loading tool, kept apart from
        # course_note_toolset so it reads as its own capability.
        self.skill_toolset = FunctionToolset()

        @self.skill_toolset.tool_plain
        def load_executive_brief_skill() -> str:
            """Load Markdown instructions for executive-brief summaries."""
            self.diagnostics.append("[skill] loaded SKILL.md")
            skill = load_skill(SKILL_PATH)
            self.trace.block("Loaded executive-brief skill (SKILL.md)", skill)
            return skill

        self.agent = PydanticAgent(
            model_name,
            instructions=SYSTEM_PROMPT,
            toolsets=[self.course_note_toolset, self.skill_toolset, self.star_wars_toolset],
        )

    # Context manager methods: start and close the remote MCP toolset.
    async def __aenter__(self) -> "CourseAssistant":
        await self.star_wars_toolset.__aenter__()
        # ... any other MCP toolsets you add here ...
        # await self.calendar_toolset.__aenter__()

        # Tool resolution normally happens invisibly inside every agent.run() call.
        # Log it once here (results are cached for the rest of the session) so the
        # tool names/descriptions/schemas actually sent to the model are visible.
        if self.trace.enabled:
            self.trace.log_system_prompt(SYSTEM_PROMPT)
            tools = describe_local_toolset(self.course_note_toolset)
            tools += describe_local_toolset(self.skill_toolset)
            remote_tools = await describe_mcp_toolset(self.star_wars_mcp)
            tools += [tool for tool in remote_tools if tool["name"] in STAR_WARS_TOOL_NAMES]
            self.trace.json("Startup — Tools resolved (cached for the rest of the session)", tools)

        return self

    async def __aexit__(self, *exc_info: object) -> None:
        try:
            await self.star_wars_toolset.__aexit__(*exc_info)
            # ... any other MCP toolsets you add here ...
            # await self.calendar_toolset.__aenter__()
        finally:
            self.trace.close()

    async def ask(self, question: str) -> str:
        """Give the model a turn; it can select local tools, MCP tools, or the skill."""
        self.diagnostics.clear()
        self.trace.begin_turn(SYSTEM_PROMPT, question, user_input=question)
        result = await self.agent.run(
            question,
            message_history=self.message_history,
            event_stream_handler=self.trace.event_stream_handler if self.trace.enabled else None,
        )
        self.message_history = result.all_messages()
        self.trace.finish_response(result.output)
        return result.output
