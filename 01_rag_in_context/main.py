"""CLI entrypoint for Part 1."""

import argparse

from agent import CourseAssistant
from config import load_model_name


def main() -> None:

    # Parses command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", action="store_true", help="save a detailed trace log")
    args = parser.parse_args()

    # Initializes the course assistant with the specified model and trace option
    assistant = CourseAssistant(load_model_name(), trace=args.trace)
    print("Part 1: RAG context is retrieved on every turn. Type quit to leave.")

    # Starts the interactive loop for user input and model response
    try:
        while True:
            question = input("\nyou> ").strip()
            if question.lower() in {"quit", "exit"}:
                break
            if not question:
                continue

            answer = assistant.ask(question)
            if not args.trace:
                print("\n".join(assistant.diagnostics))
                print(f"assistant> {answer}")
    finally:
        assistant.trace.close()


if __name__ == "__main__":
    main()
