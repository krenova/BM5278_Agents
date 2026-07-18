# Part 3 — Remote Star Wars MCP

After installing the root `requirements.txt` and configuring the root `.env`, run `python main.py`. `agent.py` keeps the same prompt, collection, `message_history`, diagnostics list, and local retrieval function as Part 2, then packages it in `course_note_toolset`. The agent receives that local toolset alongside `star_wars_toolset`, which connects over HTTPS to Pipeworx's SWAPI MCP endpoint. The model can choose tools for Star Wars people, planets, starships, and films.

Run `python main.py --trace` to save labelled instructions, memory, input, function
or MCP tool calls/results, and streamed model text to this folder's redacted `logs/`
directory. The terminal shows only the conversation.
