"""CLI entrypoint for Part 1."""

import argparse

from agent import CourseAssistant
from config import load_model_name


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", action="store_true", help="show live model and tool messages")
    args = parser.parse_args()
    assistant = CourseAssistant(load_model_name(), trace=args.trace)
    print("Part 1: RAG context is retrieved on every turn. Type quit to leave.")

    while True:
        question = input("\nyou> ").strip()
        if question.lower() in {"quit", "exit"}:
            break
        if not question:
            continue

        answer = assistant.ask(question)
        if args.trace:
            print()
        else:
            print("\n".join(assistant.diagnostics))
            print(f"assistant> {answer}")


if __name__ == "__main__":
    main()
