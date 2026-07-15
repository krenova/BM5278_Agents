"""Part 2 assistant: retrieval is a model-selected Pydantic AI function tool."""

from dataclasses import dataclass, field
from trace import LiveTrace

from pydantic_ai import Agent as PydanticAgent
from pydantic_ai import RunContext
from rag import format_context, open_collection, retrieve

SYSTEM_PROMPT = """You are a helpful course assistant. You may call
search_course_notes for questions about this course, Pydantic AI, or RAG. Do not call
it for ordinary general-knowledge conversation. Explain when you used course notes."""


@dataclass
class ToolDependencies:
    """Runtime data made available to this lesson's function tools."""

    collection: object
    diagnostics: list[str] = field(default_factory=list)


class CourseAssistant:
    """Owns the prompt, session memory, dependencies, and registered tools."""

    def __init__(self, model_name: str, trace: bool = False) -> None:
        self.dependencies = ToolDependencies(collection=open_collection())
        self.message_history = []  # Pydantic AI messages retained for this CLI session.
        self.agent = self._build_agent(model_name)
        self.trace = LiveTrace(trace)

    @property
    def diagnostics(self) -> list[str]:
        """Return tool activity from the most recent turn."""
        return self.dependencies.diagnostics

    def _build_agent(self, model_name: str) -> PydanticAgent[ToolDependencies, str]:
        """Create the Pydantic AI agent and register its model-selected tools."""
        agent = PydanticAgent(model_name, deps_type=ToolDependencies, instructions=SYSTEM_PROMPT)

        @agent.tool
        def search_course_notes(ctx: RunContext[ToolDependencies], question: str) -> str:
            """Search local course notes for relevant source passages."""
            hits = retrieve(ctx.deps.collection, question)
            sources = ", ".join(hit["source"] for hit in hits)
            ctx.deps.diagnostics.append(f"[tool] search_course_notes: {sources}")
            return format_context(hits)

        return agent

    def ask(self, question: str) -> str:
        """Give the model a turn; it decides whether to use registered tools."""
        self.dependencies.diagnostics.clear()
        self.trace.begin_turn(SYSTEM_PROMPT, self.message_history, question)
        result = self.agent.run_sync(
            question,
            deps=self.dependencies,
            message_history=self.message_history,
            event_stream_handler=self.trace.event_stream_handler if self.trace.enabled else None,
        )
        self.message_history = result.all_messages()
        return result.output
