# Five-Part Pydantic AI Agent Tutorial

Each numbered folder is a standalone lesson. Start at Part 1 and move forward: each lesson keeps the previous lesson's core behavior so differences are easy to inspect.

## Setup

```bash
source .venv/bin/activate
python -m pip install -r 01_rag_in_context/requirements.txt
cp 01_rag_in_context/.env.example 01_rag_in_context/.env
```

Set `MODEL_NAME` to a Pydantic AI model identifier and set that provider's credentials. The included `.env.example` shows both an OpenAI option (`openai:gpt-4.1-mini`) and a MiniMax Anthropic-compatible option (`anthropic:MiniMax-M3` with `ANTHROPIC_BASE_URL`). Copy the `.env` setup into the other lesson folders as needed. `python-dotenv` loads `.env` when the program starts.

Run a lesson from its own folder:

```bash
cd 01_rag_in_context
python agent.py
```

Lesson order:

1. `01_rag_in_context` — retrieval is injected on every turn.
2. `02_rag_tool` — the model chooses the retrieval tool.
3. `03_mcp_weather` — adds a local stdio MCP weather tool.
4. `04_subagent_summary` — adds an executive-brief subagent.
5. `05_skill_tool` — replaces the subagent summary route with a Markdown skill.

The `.chroma/` directories are generated locally on first run and are deliberately ignored by Git. Run tests with `python -m unittest discover -s tests` inside a lesson folder.
