from __future__ import annotations
import asyncio, os, sys
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext
from pydantic_ai.mcp import MCPServerStdio
from rag import format_context, open_collection, retrieve
@dataclass
class Deps: collection: object; diagnostics: list[str]=field(default_factory=list)
INSTRUCTIONS='''You are a helpful course assistant. Use search_course_notes for course/RAG/Pydantic AI questions, and use the weather tool for current weather questions. Do not use tools for ordinary general knowledge. Mention used sources or tools.'''
async def main():
 load_dotenv(Path(__file__).parent.parent / '.env'); model=os.getenv('MODEL_NAME')
 if not model: raise SystemExit('MODEL_NAME is missing. Configure the project-root .env file.')
 # MCPServerStdio is a Pydantic AI Toolset connected to this local server.
 weather_toolset=MCPServerStdio('python', args=['weather_server.py'])
 async with weather_toolset:
  agent=Agent(model,deps_type=Deps,instructions=INSTRUCTIONS,toolsets=[weather_toolset])
  @agent.tool
  def search_course_notes(ctx:RunContext[Deps],question:str)->str:
   '''Search local course notes for relevant source passages.'''
   hits=retrieve(ctx.deps.collection,question);ctx.deps.diagnostics.append('[tool] search_course_notes: '+', '.join(x['source'] for x in hits));return format_context(hits)
  deps,history=Deps(open_collection()),[]
  print('Part 3: model-selected RAG plus local MCP weather. Type quit to leave.')
  while (q:=input('\nyou> ').strip()).lower() not in {'quit','exit'}:
   if not q:continue
   deps.diagnostics.clear(); result=await agent.run(q,deps=deps,message_history=history);history=result.all_messages()
   print('\n'.join(deps.diagnostics) if deps.diagnostics else '[tool] no local retrieval call (MCP tool calls are model-visible)');print(f'assistant> {result.output}')
if __name__=='__main__': asyncio.run(main())
