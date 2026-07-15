"""Small, inspectable ChromaDB helpers used by every lesson."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

CHUNK_SIZE = 700


def load_documents(folder: str | Path) -> list[tuple[str, str]]:
    """Return (stable-id, text) pairs for non-empty .txt files."""
    folder = Path(folder)
    return [(path.stem, path.read_text(encoding="utf-8").strip())
            for path in sorted(folder.glob("*.txt")) if path.read_text(encoding="utf-8").strip()]


def chunk_text(text: str, size: int = CHUNK_SIZE) -> list[str]:
    """Prefer paragraph boundaries while keeping chunks beginner-friendly."""
    chunks, current = [], ""
    for paragraph in text.split("\n\n"):
        candidate = f"{current}\n\n{paragraph}".strip()
        if current and len(candidate) > size:
            chunks.append(current)
            current = paragraph
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def index_documents(collection, documents: Iterable[tuple[str, str]]) -> int:
    ids, texts, metadata = [], [], []
    for source, text in documents:
        for number, chunk in enumerate(chunk_text(text)):
            ids.append(f"{source}-{number}")
            texts.append(chunk)
            metadata.append({"source": source, "chunk": number})
    if ids:
        collection.upsert(ids=ids, documents=texts, metadatas=metadata)
    return len(ids)


def retrieve(collection, question: str, limit: int = 3) -> list[dict]:
    result = collection.query(query_texts=[question], n_results=limit, include=["documents", "metadatas", "distances"])
    return [{"text": text, "source": metadata["source"], "distance": distance}
            for text, metadata, distance in zip(result["documents"][0], result["metadatas"][0], result["distances"][0])]


def format_context(hits: list[dict]) -> str:
    if not hits:
        return "No course-note matches were found."
    return "\n\n".join(f"[{hit['source']}]\n{hit['text']}" for hit in hits)


def open_collection(base: str | Path = ".chroma"):
    import chromadb
    client = chromadb.PersistentClient(path=str(base))
    collection = client.get_or_create_collection("course_notes")
    index_documents(collection, load_documents(Path(__file__).parent / "documents"))
    return collection
