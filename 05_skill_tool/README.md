# Part 5 — Markdown skill tool

After installing the root `requirements.txt` and configuring the root `.env`, run `python main.py`. In `agent.py`, `SYSTEM_PROMPT`, `message_history`, and `_build_agent()` identify prompts, memory, and tools. This lesson deliberately has no summary subagent: for a summary the main agent calls `load_executive_brief_skill`, reads `SKILL.md`, and applies those instructions itself.

Run `python main.py --trace` to show all observable messages, tool calls/results,
and streamed text. When the summary skill is loaded, the full `SKILL.md` content is labelled separately.
