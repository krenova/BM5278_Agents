# Part 1 — RAG in the prompt

From the project root, install `-r requirements.txt` once and copy `.env.example` to `.env` once. Configure one model option there, then run `python main.py` from this folder.

Read `agent.py` to see the prompt in `SYSTEM_PROMPT`, session memory in `message_history`, and the prompt-injection retrieval step in `CourseAssistant.ask()`. Each user turn retrieves local ChromaDB matches before calling the model.

Run `python main.py --trace` to save the instructions, saved messages, full
retrieval-expanded model input, and streamed model text to a redacted log file in
`logs/`. The terminal continues to show only the conversation. Files are named
like `trace_20260718-143012_01_rag_in_context.log` and contain observable messages
only, not hidden reasoning.
