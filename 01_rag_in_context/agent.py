"""Part 1 assistant: retrieval is inserted into every model prompt."""

from trace import LiveTrace

from pydantic_ai import Agent as PydanticAgent
from rag import format_context, open_collection, retrieve

SYSTEM_PROMPT = """You are a helpful course assistant. Use the supplied course-note
context when relevant. Say when the notes do not answer a question; answer general
questions normally."""


class CourseAssistant:
    """Owns the prompt, conversation memory, and retrieval context for Part 1."""

    def __init__(self, model_name: str, trace: bool = False) -> None:
        self.agent = PydanticAgent(model_name, instructions=SYSTEM_PROMPT)
        self.collection = open_collection()
        self.message_history = []  # Pydantic AI messages retained for this CLI session.
        self.diagnostics: list[str] = []
        self.trace = LiveTrace(trace)

    def ask(self, question: str) -> str:
        """Retrieve notes, add them to the prompt, and save the resulting memory."""
        hits = retrieve(self.collection, question)
        self.diagnostics = [
            "[retrieval] " + ", ".join(f"{hit['source']} ({hit['distance']:.3f})" for hit in hits)
        ]
        prompt = f"Course-note context:\n{format_context(hits)}\n\nUser question: {question}"
        self.trace.begin_turn(SYSTEM_PROMPT, self.message_history, prompt)
        result = self.agent.run_sync(
            prompt,
            message_history=self.message_history,
            event_stream_handler=self.trace.event_stream_handler if self.trace.enabled else None,
        )
        self.message_history = result.all_messages()
        return result.output
