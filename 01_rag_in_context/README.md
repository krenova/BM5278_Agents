# Part 1 — RAG in the prompt

Install `-r requirements.txt`, copy `.env.example` to `.env`, configure `MODEL_NAME` and the provider key, then run `python agent.py`. Each user turn retrieves the top local ChromaDB matches and prints them before injecting them into the prompt.
