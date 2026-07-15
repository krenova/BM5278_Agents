# Five-Part Pydantic AI Agent Tutorial

Each numbered folder is a standalone lesson. Start at Part 1 and move forward: each lesson keeps the previous lesson's core behavior so differences are easy to inspect.

## Setup

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Set exactly one active `MODEL_NAME` and its matching credentials. The included root `.env.example` shows both an OpenAI option (`openai:gpt-4.1-mini`) and a MiniMax Anthropic-compatible option (`anthropic:MiniMax-M3` with `ANTHROPIC_BASE_URL`). Every lesson explicitly loads this one root `.env`; do not create per-lesson `.env` files.

Run a lesson from its own folder:

```bash
cd 01_rag_in_context
python main.py
```

For a teaching-oriented live trace, run `python main.py --trace`. It prints the
agent instructions, prior session messages, new model input, tool calls and
results, and streamed model text. Trace output is terminal-only and shows
observable exchanges, not hidden model reasoning; credentials are redacted.

Lesson order:

1. `01_rag_in_context` — retrieval is injected on every turn.
2. `02_rag_tool` — the model chooses the retrieval tool.
3. `03_mcp_weather` — adds a local stdio MCP weather tool.
4. `04_subagent_summary` — adds an executive-brief subagent.
5. `05_skill_tool` — replaces the subagent summary route with a Markdown skill.

Every lesson uses the same teaching layout:

- `main.py` is the small CLI entrypoint.
- `agent.py` contains the stateful `CourseAssistant`: its prompt constants, `message_history`, tool registration, and `ask()` method.
- `config.py` loads the shared project-root `.env`.
- `rag.py` contains local document indexing and retrieval; Parts 3–5 also include `weather_server.py`.

The `.chroma/` directories are generated locally on first run and are deliberately ignored by Git. Run tests with `python -m unittest discover -s tests` inside a lesson folder. Check formatting and linting from the root with `ruff format --check .` and `ruff check .`.
