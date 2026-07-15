# Part 5 — Markdown skill tool

After installing the root `requirements.txt` and configuring the root `.env`, run `python agent.py`. This lesson retains Part 3's retrieval and MCP weather behavior. It deliberately has no summary subagent: for a summary the main agent calls `load_executive_brief_skill`, reads `SKILL.md`, and applies those instructions itself.
