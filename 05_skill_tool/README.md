# Part 5 — Markdown skill tool

After installing the root `requirements.txt` and configuring the root `.env`, run `python main.py`. In `agent.py`, `SYSTEM_PROMPT`, `message_history`, and `course_note_toolset` are unchanged from Part 3; a new `skill_toolset` holds a single `load_executive_brief_skill` tool, kept separate so it reads as its own capability rather than another course-note function. This lesson deliberately has no summary subagent: for a summary the main agent calls `load_executive_brief_skill`, reads `SKILL.md`, and applies those instructions itself — including `SKILL.md`'s Yoda persona, so the brief keeps the same `## Key points` / `## Risks` / `## Recommended actions` structure as Part 4's subagent brief but in Yoda's speech pattern.

Run `python main.py --trace` to save all observable messages, tool calls/results,
and streamed text to this folder's redacted `logs/` directory. The terminal shows
only the conversation. When the summary skill is loaded, the full `SKILL.md` content
is labelled separately in the log.
