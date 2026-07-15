# Part 1 — RAG in the prompt

From the project root, install `-r requirements.txt` once and copy `.env.example` to `.env` once. Configure one model option there, then run `python agent.py` from this folder. Each user turn retrieves the top local ChromaDB matches and prints them before injecting them into the prompt.
