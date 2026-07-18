# Part 4 — Summary subagent

After installing the root `requirements.txt` and configuring the root `.env`, `python main.py` retains Part 3's RAG and remote Star Wars MCP behavior. In `agent.py`, `course_note_toolset` and `star_wars_toolset` are unchanged from Part 3; a new `brief_toolset` holds a single `create_executive_brief` tool, kept separate so it reads as its own capability rather than another course-note function. Calling that tool delegates the material to `brief_agent`, a focused Pydantic AI subagent that only ever sees the text handed to it, not the parent's conversation history. `BRIEF_PROMPT` gives that subagent a Yoda persona, so the resulting brief keeps the same `## Key points` / `## Risks` / `## Recommended actions` structure but is written in Yoda's speech pattern.

Run `python main.py --trace` to save parent and subagent instructions, the labelled
parent-to-subagent handoff, tool calls/results, and streamed model text to this
folder's redacted `logs/` directory. The terminal shows only the parent conversation.
