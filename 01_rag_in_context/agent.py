from __future__ import annotations

import os
from dotenv import load_dotenv
from pydantic_ai import Agent
from rag import format_context, open_collection, retrieve

INSTRUCTIONS = """You are a helpful course assistant. Use the supplied course-note context when relevant. Say when the notes do not answer a question; answer general questions normally."""


def main() -> None:
    load_dotenv()
    model = os.getenv("MODEL_NAME")
    if not model:
        raise SystemExit("MODEL_NAME is missing. Copy .env.example to .env and configure it.")
    agent = Agent(model, instructions=INSTRUCTIONS)
    collection, history = open_collection(), []
    print("Part 1: RAG context is retrieved on every turn. Type quit to leave.")
    while (question := input("\nyou> ").strip()).lower() not in {"quit", "exit"}:
        if not question:
            continue
        hits = retrieve(collection, question)
        print("[retrieval] " + ", ".join(f"{h['source']} ({h['distance']:.3f})" for h in hits))
        prompt = f"Course-note context:\n{format_context(hits)}\n\nUser question: {question}"
        result = agent.run_sync(prompt, message_history=history)
        history = result.all_messages()
        print(f"assistant> {result.output}")


if __name__ == "__main__":
    main()
