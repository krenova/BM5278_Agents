"""Part 2 assistant: retrieval is a model-selected Pydantic AI function tool."""

from trace import LiveTrace, describe_local_toolset

from pydantic_ai import Agent as PydanticAgent
from pydantic_ai import FunctionToolset
from rag import format_context, open_collection, retrieve

SYSTEM_PROMPT = """You are a helpful course assistant. You may call
search_course_notes for questions about this course, Pydantic AI, or RAG. Do not call
it for ordinary general-knowledge conversation. Explain when you used course notes."""


class CourseAssistant:
    """Owns the prompt, session memory, retrieval collection, and registered tool."""

    def __init__(self, model_name: str, trace: bool = False) -> None:
        self.collection = open_collection()  # Chroma collection for course-note retrieval.
        self.message_history = []  # Pydantic AI messages retained for this CLI session.
        self.diagnostics: list[str] = []  # Tool diagnostics shown when tracing is off.
        self.trace = LiveTrace(trace)

        self.course_note_toolset = FunctionToolset()

        @self.course_note_toolset.tool_plain
        def search_course_notes(question: str) -> str:
            """Search local course notes for relevant source passages."""
            hits = retrieve(self.collection, question)
            sources = ", ".join(hit["source"] for hit in hits)
            self.diagnostics.append(f"[tool] search_course_notes: {sources}")
            return format_context(hits)

        # Tool resolution normally happens invisibly inside every agent.run() call.
        # Log it once here so its name/description/schema are visible in the trace.
        if self.trace.enabled:
            self.trace.log_system_prompt(SYSTEM_PROMPT)
            self.trace.json(
                "Startup — Tools resolved (cached for the rest of the session)",
                describe_local_toolset(self.course_note_toolset),
            )

        # The main agent can use the local course-note toolset.
        self.agent = PydanticAgent(
            model_name,
            instructions=SYSTEM_PROMPT,
            toolsets=[self.course_note_toolset],
        )

    def ask(self, question: str) -> str:
        """Give the model a turn; it decides whether to use registered tools."""
        self.diagnostics.clear()
        self.trace.begin_turn(SYSTEM_PROMPT, question, user_input=question)
        result = self.agent.run_sync(
            question,
            message_history=self.message_history,
            event_stream_handler=self.trace.event_stream_handler if self.trace.enabled else None,
        )
        self.message_history = result.all_messages()
        self.trace.finish_response(result.output)
        return result.output
