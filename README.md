# Five-Part Pydantic AI Agent Tutorial

Each numbered folder is a standalone lesson. Start at Part 1 and move forward: each lesson keeps the previous lesson's core behavior so differences are easy to inspect.

The shared `shared_trace.py` module implements trace logging once for all lessons.
Each lesson's small `trace.py` adapter supplies its own folder for log placement while
preserving standalone `python main.py` runs.

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

For a teaching-oriented trace log, run `python main.py --trace`. The terminal
still shows only the conversation, while a detailed, credential-redacted record
of instructions, memory, model input, tool calls/results, and observable model
text is saved in that lesson's `logs/` folder. Each session file is named like
`trace_20260718-143012_03_mcp_starwars.log`; it shows observable exchanges, not
hidden model reasoning. The log is grouped into numbered conversation turns; every
turn starts with the exact user message and records the expanded input sent to the
model, including retrieved context where applicable.

Lesson order:

1. `01_rag_in_context` — retrieval is injected on every turn.
2. `02_rag_tool` — the model chooses the retrieval tool.
3. `03_mcp_starwars` — adds a remote HTTPS MCP toolset for Star Wars data.
4. `04_subagent_summary` — adds an executive-brief subagent.
5. `05_skill_tool` — replaces the subagent summary route with a Markdown skill.

Every lesson uses the same teaching layout:

- `main.py` is the small CLI entrypoint.
- `agent.py` contains the stateful `CourseAssistant`: its prompt constants, `message_history`, tool registration, and `ask()` method.
- `config.py` loads the shared project-root `.env`.
- `rag.py` contains local document indexing and retrieval; Parts 3–5 connect to a remote Star Wars MCP toolset over HTTPS instead of running a local server.

The `.chroma/` directories are generated locally on first run and are deliberately ignored by Git. Run tests with `python -m unittest discover -s tests` inside a lesson folder. Check formatting and linting from the root with `ruff format --check .` and `ruff check .`.
