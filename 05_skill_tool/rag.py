from pathlib import Path
def load_documents(folder):return [(p.stem,p.read_text(encoding='utf-8').strip()) for p in sorted(Path(folder).glob('*.txt')) if p.read_text(encoding='utf-8').strip()]
def chunk_text(text,size=700):
 o=[];cur=''
 for p in text.split('\n\n'):
  x=f'{cur}\n\n{p}'.strip()
  if cur and len(x)>size:o.append(cur);cur=p
  else:cur=x
 return o+([cur] if cur else [])
def index_documents(c,docs):
 ids=[];ts=[];ms=[]
 for s,t in docs:
  for i,x in enumerate(chunk_text(t)):ids.append(f'{s}-{i}');ts.append(x);ms.append({'source':s,'chunk':i})
 if ids:c.upsert(ids=ids,documents=ts,metadatas=ms)
 return len(ids)
def retrieve(c,q,limit=3):
 r=c.query(query_texts=[q],n_results=limit,include=['documents','metadatas','distances']);return [{'text':t,'source':m['source'],'distance':d} for t,m,d in zip(r['documents'][0],r['metadatas'][0],r['distances'][0])]
def format_context(h):return '\n\n'.join(f"[{x['source']}]\n{x['text']}" for x in h) or 'No course-note matches were found.'
def open_collection(base='.chroma'):
 import chromadb
 c=chromadb.PersistentClient(path=str(base)).get_or_create_collection('course_notes');index_documents(c,load_documents(Path(__file__).parent/'documents'));return c
