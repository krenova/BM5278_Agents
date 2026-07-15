from __future__ import annotations
import asyncio,os
from dataclasses import dataclass,field
from pathlib import Path
from dotenv import load_dotenv
from pydantic_ai import Agent,RunContext
from pydantic_ai.mcp import MCPServerStdio
from rag import open_collection,retrieve,format_context
@dataclass
class Deps: collection:object; diagnostics:list[str]=field(default_factory=list); usage:object|None=None
PARENT='''You are a helpful course assistant. Use search_course_notes for course questions and the weather tool for current weather. For an executive brief or summary, call create_executive_brief. Mention tool use.'''
BRIEF='''Create an executive brief using exactly these Markdown headings: ## Key points, ## Risks, ## Recommended actions. Be concise and preserve uncertainty.''' 
async def main():
 load_dotenv(Path(__file__).parent.parent / '.env');model=os.getenv('MODEL_NAME')
 if not model:raise SystemExit('MODEL_NAME is missing. Configure the project-root .env file.')
 weather=MCPServerStdio('python',args=['weather_server.py'])
 async with weather:
  parent=Agent(model,deps_type=Deps,instructions=PARENT,toolsets=[weather]);brief_agent=Agent(model,instructions=BRIEF)
  @parent.tool
  def search_course_notes(ctx:RunContext[Deps],question:str)->str:
   '''Search local course notes.'''
   hits=retrieve(ctx.deps.collection,question);ctx.deps.diagnostics.append('[tool] search_course_notes');return format_context(hits)
  @parent.tool
  async def create_executive_brief(ctx:RunContext[Deps],material:str)->str:
   '''Delegate material to a specialist that creates an executive brief.'''
   ctx.deps.diagnostics.append('[subagent] executive brief')
   result=await brief_agent.run(material,usage=ctx.usage)
   ctx.deps.usage=result.usage();return result.output
  deps,history=Deps(open_collection()),[]
  print('Part 4: model-selected RAG/weather plus executive-brief subagent. Type quit to leave.')
  while (q:=input('\nyou> ').strip()).lower() not in {'quit','exit'}:
   if not q:continue
   deps.diagnostics.clear();result=await parent.run(q,deps=deps,message_history=history,usage=deps.usage);deps.usage=result.usage();history=result.all_messages()
   print('\n'.join(deps.diagnostics) if deps.diagnostics else '[tool] no local tool call');print(f'assistant> {result.output}')
if __name__=='__main__':asyncio.run(main())
