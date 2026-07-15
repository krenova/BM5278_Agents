# Part 2 — Model-selected RAG tool

Install the root `requirements.txt` and configure the single root `.env`, then run `python main.py` from this folder. In `agent.py`, `SYSTEM_PROMPT` shows the instructions, `message_history` stores the session, and `_build_agent()` shows where `search_course_notes` is registered. Unlike Part 1, the model calls that tool only when it considers the notes useful.

Use `python main.py --trace` to show instructions, memory, model input, each tool
call with JSON arguments, each result sent back to the model, and streamed text.
