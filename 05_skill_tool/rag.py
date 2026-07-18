"""Local ChromaDB retrieval helpers for this lesson."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, TypedDict

CHUNK_SIZE = 700
LESSON_DIR = Path(__file__).parent
DOCUMENTS_DIR = LESSON_DIR / "documents"
INDEX_DIR = LESSON_DIR / ".chroma"


class RetrievalHit(TypedDict):
    """A source passage returned by the local vector index."""

    text: str
    source: str
    distance: float


def load_documents(folder: str | Path) -> list[tuple[str, str]]:
    """Return stable source IDs and text from non-empty .txt files."""
    documents: list[tuple[str, str]] = []
    for path in sorted(Path(folder).glob("*.txt")):
        text = path.read_text(encoding="utf-8").strip()
        if text:
            documents.append((path.stem, text))
    return documents


def chunk_text(text: str, size: int = CHUNK_SIZE) -> list[str]:
    """Split text on paragraph boundaries without exceeding the target where possible."""
    chunks: list[str] = []
    current = ""
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


def index_documents(collection: object, documents: Iterable[tuple[str, str]]) -> int:
    """Upsert all document chunks and return the number of indexed chunks."""
    ids: list[str] = []
    texts: list[str] = []
    metadatas: list[dict[str, str | int]] = []
    for source, text in documents:
        for chunk_number, chunk in enumerate(chunk_text(text)):
            ids.append(f"{source}-{chunk_number}")
            texts.append(chunk)
            metadatas.append({"source": source, "chunk": chunk_number})
    if ids:
        collection.upsert(ids=ids, documents=texts, metadatas=metadatas)
    return len(ids)


def retrieve(collection: object, question: str, limit: int = 3) -> list[RetrievalHit]:
    """Retrieve the closest course-note chunks for a question."""
    result = collection.query(
        query_texts=[question],
        n_results=limit,
        include=["documents", "metadatas", "distances"],
    )
    return [
        {"text": text, "source": metadata["source"], "distance": distance}
        for text, metadata, distance in zip(
            result["documents"][0],
            result["metadatas"][0],
            result["distances"][0],
            strict=True,
        )
    ]


def format_context(hits: list[RetrievalHit]) -> str:
    """Render retrieved notes and their distances for a model prompt or tool result."""
    if not hits:
        return "No course-note matches were found."
    return "\n\n".join(
        f"[{hit['source']} | retrieval distance: {hit['distance']:.3f}]\n{hit['text']}"
        for hit in hits
    )


def open_collection(base: str | Path = INDEX_DIR) -> object:
    """Open this lesson's persistent Chroma collection and refresh its source documents."""
    import chromadb

    client = chromadb.PersistentClient(path=str(base))
    collection = client.get_or_create_collection("course_notes")
    index_documents(collection, load_documents(DOCUMENTS_DIR))
    return collection
