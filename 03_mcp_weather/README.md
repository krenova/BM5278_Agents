# Part 3 — MCP weather

After installing the root `requirements.txt` and configuring the root `.env`, run `python main.py`. `agent.py` makes the prompt, `message_history`, local retrieval tool, and `weather_toolset` explicit. The agent starts `weather_server.py` as a local stdio MCP process; the server calls Open-Meteo only when the model chooses `get_weather` and sends diagnostics to stderr.

Run `python main.py --trace` for labelled instructions, memory, input, function or
MCP tool calls and results, and streamed model text. MCP protocol stdout remains untouched.
