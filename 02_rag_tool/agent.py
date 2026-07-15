from __future__ import annotations
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext
from rag import format_context, open_collection, retrieve

@dataclass
class Deps:
    collection: object
    diagnostics: list[str] = field(default_factory=list)

INSTRUCTIONS = """You are a helpful course assistant. You may call search_course_notes for questions about this course, Pydantic AI, or RAG. Do not call it for ordinary general-knowledge conversation. Explain when you used course notes."""

def main():
    load_dotenv(); model=os.getenv('MODEL_NAME')
    if not model: raise SystemExit('MODEL_NAME is missing. Copy .env.example to .env and configure it.')
    agent=Agent(model, deps_type=Deps, instructions=INSTRUCTIONS)
    @agent.tool
    def search_course_notes(ctx: RunContext[Deps], question: str) -> str:
        """Search the local course notes for relevant source passages."""
        hits=retrieve(ctx.deps.collection, question)
        ctx.deps.diagnostics.append('[tool] search_course_notes: ' + ', '.join(h['source'] for h in hits))
        return format_context(hits)
    deps, history=Deps(open_collection()), []
    print('Part 2: the model decides when to search notes. Type quit to leave.')
    while (question:=input('\nyou> ').strip()).lower() not in {'quit','exit'}:
        if not question: continue
        deps.diagnostics.clear(); result=agent.run_sync(question, deps=deps, message_history=history); history=result.all_messages()
        print('\n'.join(deps.diagnostics) if deps.diagnostics else '[tool] no retrieval call')
        print(f'assistant> {result.output}')
if __name__ == '__main__': main()
