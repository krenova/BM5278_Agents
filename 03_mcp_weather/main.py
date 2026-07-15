"""CLI entrypoint for Part 3."""

import argparse
import asyncio

from agent import CourseAssistant
from config import load_model_name


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", action="store_true", help="show live model and tool messages")
    args = parser.parse_args()
    async with CourseAssistant(load_model_name(), trace=args.trace) as assistant:
        print("Part 3: model-selected RAG plus local MCP weather. Type quit to leave.")

        while True:
            question = input("\nyou> ").strip()
            if question.lower() in {"quit", "exit"}:
                break
            if not question:
                continue

            answer = await assistant.ask(question)
            if args.trace:
                print()
            else:
                diagnostic = "\n".join(assistant.diagnostics)
                print(diagnostic or "[tool] no local retrieval call")
                print(f"assistant> {answer}")


if __name__ == "__main__":
    asyncio.run(main())
