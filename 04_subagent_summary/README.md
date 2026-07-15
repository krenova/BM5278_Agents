# Part 4 — Summary subagent

After installing the root `requirements.txt` and configuring the root `.env`, `python main.py` retains Part 3's RAG and MCP weather behavior. In `agent.py`, `PARENT_PROMPT`, parent `message_history`, `_build_parent_agent()`, and `brief_agent` make the orchestration explicit. For executive-brief requests the parent invokes the focused Pydantic AI subagent and shares usage tracking with it.

Run `python main.py --trace` to see parent and subagent instructions, the labelled
parent-to-subagent handoff, tool calls/results, and streamed model text.
