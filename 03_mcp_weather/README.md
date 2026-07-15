# Part 3 — MCP weather

Run `python agent.py`. The agent starts `weather_server.py` as a local stdio MCP process. The server calls Open-Meteo only when the model chooses `get_weather`; its diagnostics go to stderr so the MCP protocol remains valid.
