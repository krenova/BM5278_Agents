"""CLI entrypoint for Part 4."""

import argparse
import asyncio

from agent import CourseAssistant
from config import load_model_name


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", action="store_true", help="show live model and tool messages")
    args = parser.parse_args()
    async with CourseAssistant(load_model_name(), trace=args.trace) as assistant:
        print("Part 4: RAG/weather plus executive-brief subagent. Type quit to leave.")

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
                print("\n".join(assistant.diagnostics) or "[tool] no local tool call")
                print(f"assistant> {answer}")


if __name__ == "__main__":
    asyncio.run(main())
