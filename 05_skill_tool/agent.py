from __future__ import annotations
import asyncio,os
from dataclasses import dataclass,field
from pathlib import Path
from dotenv import load_dotenv
from pydantic_ai import Agent,RunContext
from pydantic_ai.mcp import MCPServerStdio
from rag import open_collection,retrieve,format_context
from skill_loader import load_skill
@dataclass
class Deps: collection:object;diagnostics:list[str]=field(default_factory=list)
INSTRUCTIONS='''You are a helpful course assistant. Use search_course_notes for course questions and the weather tool for current weather. For an executive brief or summary, call load_executive_brief_skill, then follow its instructions yourself. Mention tool use.'''
async def main():
 load_dotenv(Path(__file__).parent.parent / '.env');model=os.getenv('MODEL_NAME')
 if not model:raise SystemExit('MODEL_NAME is missing. Configure the project-root .env file.')
 weather=MCPServerStdio('python',args=['weather_server.py'])
 async with weather:
  agent=Agent(model,deps_type=Deps,instructions=INSTRUCTIONS,toolsets=[weather])
  @agent.tool
  def search_course_notes(ctx:RunContext[Deps],question:str)->str:
   '''Search local course notes.'''
   h=retrieve(ctx.deps.collection,question);ctx.deps.diagnostics.append('[tool] search_course_notes');return format_context(h)
  @agent.tool
  def load_executive_brief_skill(ctx:RunContext[Deps])->str:
   '''Load the Markdown instructions for executive-brief summaries.'''
   ctx.deps.diagnostics.append('[skill] loaded SKILL.md');return load_skill('SKILL.md')
  deps,history=Deps(open_collection()),[]
  print('Part 5: RAG/weather plus Markdown-backed summary skill. Type quit to leave.')
  while (q:=input('\nyou> ').strip()).lower() not in {'quit','exit'}:
   if not q:continue
   deps.diagnostics.clear();r=await agent.run(q,deps=deps,message_history=history);history=r.all_messages();print('\n'.join(deps.diagnostics) if deps.diagnostics else '[tool] no local tool call');print(f'assistant> {r.output}')
if __name__=='__main__':asyncio.run(main())
