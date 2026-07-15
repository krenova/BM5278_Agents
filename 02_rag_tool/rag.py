from pathlib import Path
from typing import Iterable
CHUNK_SIZE = 700
def load_documents(folder):
    folder = Path(folder); return [(p.stem, p.read_text(encoding='utf-8').strip()) for p in sorted(folder.glob('*.txt')) if p.read_text(encoding='utf-8').strip()]
def chunk_text(text, size=CHUNK_SIZE):
    chunks, current = [], ''
    for paragraph in text.split('\n\n'):
        candidate = f'{current}\n\n{paragraph}'.strip()
        if current and len(candidate) > size: chunks.append(current); current = paragraph
        else: current = candidate
    return chunks + ([current] if current else [])
def index_documents(collection, documents: Iterable):
    ids=[]; texts=[]; meta=[]
    for source, text in documents:
        for n, chunk in enumerate(chunk_text(text)): ids.append(f'{source}-{n}'); texts.append(chunk); meta.append({'source':source,'chunk':n})
    if ids: collection.upsert(ids=ids, documents=texts, metadatas=meta)
    return len(ids)
def retrieve(collection, question, limit=3):
    result=collection.query(query_texts=[question], n_results=limit, include=['documents','metadatas','distances'])
    return [{'text':t,'source':m['source'],'distance':d} for t,m,d in zip(result['documents'][0],result['metadatas'][0],result['distances'][0])]
def format_context(hits): return '\n\n'.join(f"[{h['source']}]\n{h['text']}" for h in hits) or 'No course-note matches were found.'
def open_collection(base='.chroma'):
    import chromadb
    collection=chromadb.PersistentClient(path=str(base)).get_or_create_collection('course_notes')
    index_documents(collection, load_documents(Path(__file__).parent/'documents')); return collection
