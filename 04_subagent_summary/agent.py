"""Part 4 assistant: Star Wars MCP tools plus an executive-brief subagent."""

from trace import LiveTrace, describe_local_toolset, describe_mcp_toolset

from pydantic_ai import Agent as PydanticAgent
from pydantic_ai import FunctionToolset
from pydantic_ai.mcp import MCPToolset, StreamableHttpTransport
from rag import format_context, open_collection, retrieve

SYSTEM_PROMPT = """You are a helpful course assistant. Use search_course_notes for
course questions and Star Wars tools for questions about characters, planets,
starships, or films. For an executive brief or summary, call create_executive_brief
and reply with its returned text unchanged, character for character, as your
entire answer: no added title, no reformatted headings, no paraphrasing. Mention
tool use."""
BRIEF_PROMPT = """You are Yoda, Jedi Master, summarizing material for a busy executive.
Create a brief using exactly these Markdown headings: ## Key points, ## Risks,
## Recommended actions. Every sentence, in Yoda's speech pattern write you must:
inverted word order, wise and terse. Concise remain, and uncertainty preserve. Break
character, you must not."""
STAR_WARS_MCP_URL = "https://gateway.pipeworx.io/swapi/mcp"
# The gateway is a shared multi-domain router that bundles in ~20 unrelated tools
# (SEC filings, prediction markets, drug data, ...) alongside these four; keep the
# model's tool list scoped to what this lesson is actually about.
STAR_WARS_TOOL_NAMES = {"search_people", "get_planet", "get_starship", "get_film"}


class CourseAssistant:
    """Owns the Part 3 state plus a Yoda-voiced Pydantic AI subagent for executive briefs."""

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

        # A separate toolset for the single subagent-delegation tool, kept apart
        # from course_note_toolset so it reads as its own capability.
        self.brief_toolset = FunctionToolset()

        # A focused subagent that only ever sees the material handed to it, not
        # the parent's conversation history.
        self.brief_agent = PydanticAgent(model_name, instructions=BRIEF_PROMPT)

        @self.brief_toolset.tool_plain
        async def create_executive_brief(material: str) -> str:
            """Delegate material to a specialist that creates an executive brief."""
            self.diagnostics.append("[subagent] executive brief")
            self.trace.subagent_handoff(material)
            self.trace.begin_turn(
                BRIEF_PROMPT,
                [],
                material,
                label="Executive-brief subagent",
                conversation_turn=False,
            )
            result = await self.brief_agent.run(
                material,
                event_stream_handler=self.trace.log_event_stream_handler
                if self.trace.enabled
                else None,
            )
            self.trace.resume_conversation_turn("Parent agent")
            return result.output

        self.agent = PydanticAgent(
            model_name,
            instructions=SYSTEM_PROMPT,
            toolsets=[self.course_note_toolset, self.brief_toolset, self.star_wars_toolset],
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
            tools += describe_local_toolset(self.brief_toolset)
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
        """Give the model a turn; it can select local tools, MCP tools, or the subagent."""
        self.diagnostics.clear()
        self.trace.begin_turn(
            SYSTEM_PROMPT,
            self.message_history,
            question,
            label="Parent agent",
            user_input=question,
        )
        result = await self.agent.run(
            question,
            message_history=self.message_history,
            event_stream_handler=self.trace.event_stream_handler if self.trace.enabled else None,
        )
        self.message_history = result.all_messages()
        self.trace.finish_response(result.output)
        return result.output
