# Part 4 — Summary subagent

`python agent.py` retains Part 3's RAG and MCP weather behavior. For executive-brief requests the parent invokes a focused Pydantic AI subagent. The tool diagnostic makes delegation visible; the usage object is passed into the subagent run.
