# Part 1 — RAG in the prompt

From the project root, install `-r requirements.txt` once and copy `.env.example` to `.env` once. Configure one model option there, then run `python main.py` from this folder.

Read `agent.py` to see the prompt in `SYSTEM_PROMPT`, session memory in `message_history`, and the prompt-injection retrieval step in `CourseAssistant.ask()`. Each user turn retrieves local ChromaDB matches before calling the model.

Run `python main.py --trace` to see the instructions, saved messages, and the full
retrieval-expanded model input, followed by streamed model text. Trace labels show
observable messages only (not hidden reasoning), with credentials redacted.
