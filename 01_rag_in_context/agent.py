"""Part 1 assistant: retrieval is inserted into every model prompt."""

from trace import LiveTrace

from pydantic_ai import Agent as PydanticAgent
from rag import format_context, open_collection, retrieve

SYSTEM_PROMPT = """You are a helpful course assistant. Use the supplied course-note
context when relevant. Say when the notes do not answer a question; answer general
questions normally."""


class CourseAssistant:
    """Owns the prompt, conversation memory, and retrieval context for Part 1."""

    # Constructor
    def __init__(self, model_name: str, trace: bool = False) -> None:
        self.agent = PydanticAgent(model_name, instructions=SYSTEM_PROMPT)
        self.collection = (
            open_collection()
        )  # Initialize the Chroma collection for course-note retrieval.
        self.message_history = []  # Pydantic AI messages retained for this CLI session.
        self.diagnostics: list[
            str
        ] = []  # Diagnostics for the last retrieval and model run, shown when tracing is off.
        self.trace = LiveTrace(trace)
        self.trace.log_system_prompt(SYSTEM_PROMPT)

    # Method: take a question, retrieve notes, and return an answer
    def ask(self, question: str) -> str:
        """Retrieve notes, add them to the prompt, and save the resulting memory."""

        # 1. Retrieve the closest course-note chunks for the question
        hits = retrieve(self.collection, question)

        # 2. Save the retrieval diagnostics and run the model with the context
        self.diagnostics = [
            "[retrieval] " + ", ".join(f"{hit['source']} ({hit['distance']:.3f})" for hit in hits)
        ]

        # 3. Format the context and run the model with the context
        prompt = f"Course-note context:\n{format_context(hits)}\n\nUser question: {question}"

        # 4. If tracing is enabled, show the system prompt, message history, and prompt
        self.trace.begin_turn(SYSTEM_PROMPT, prompt, user_input=question)

        # 5. Run the model with the context
        result = self.agent.run_sync(
            prompt,
            message_history=self.message_history,
            event_stream_handler=self.trace.event_stream_handler if self.trace.enabled else None,
        )

        # 6. Save the resulting message history and return the model's output
        self.message_history = result.all_messages()
        self.trace.finish_response(result.output)
        return result.output
