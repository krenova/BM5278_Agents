from pathlib import Path
CHUNK_SIZE=700
def load_documents(folder):
 folder=Path(folder); return [(p.stem,p.read_text(encoding='utf-8').strip()) for p in sorted(folder.glob('*.txt')) if p.read_text(encoding='utf-8').strip()]
def chunk_text(text,size=CHUNK_SIZE):
 out=[]; current=''
 for paragraph in text.split('\n\n'):
  candidate=f'{current}\n\n{paragraph}'.strip()
  if current and len(candidate)>size: out.append(current); current=paragraph
  else: current=candidate
 return out+([current] if current else [])
def index_documents(c,documents):
 ids=[]; texts=[]; metadatas=[]
 for src,text in documents:
  for i,chunk in enumerate(chunk_text(text)): ids.append(f'{src}-{i}');texts.append(chunk);metadatas.append({'source':src,'chunk':i})
 if ids:c.upsert(ids=ids,documents=texts,metadatas=metadatas)
 return len(ids)
def retrieve(c,q,limit=3):
 r=c.query(query_texts=[q],n_results=limit,include=['documents','metadatas','distances'])
 return [{'text':t,'source':m['source'],'distance':d} for t,m,d in zip(r['documents'][0],r['metadatas'][0],r['distances'][0])]
def format_context(h):return '\n\n'.join(f"[{x['source']}]\n{x['text']}" for x in h) or 'No course-note matches were found.'
def open_collection(base='.chroma'):
 import chromadb
 c=chromadb.PersistentClient(path=str(base)).get_or_create_collection('course_notes');index_documents(c,load_documents(Path(__file__).parent/'documents'));return c
