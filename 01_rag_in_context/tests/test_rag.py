import unittest
from pathlib import Path

from rag import chunk_text, format_context, index_documents, load_documents, retrieve


class FakeCollection:
    def upsert(self, **kwargs):
        self.upserted = kwargs

    def query(self, **kwargs):
        return {
            "documents": [["retrieved text"]],
            "metadatas": [[{"source": "notes"}]],
            "distances": [[0.12]],
        }


class RagTests(unittest.TestCase):
    def test_load_and_chunk(self):
        self.assertTrue(load_documents(Path(__file__).parents[1] / "documents"))
        self.assertEqual(chunk_text("one\n\ntwo", 20), ["one\n\ntwo"])

    def test_index_and_retrieve(self):
        collection = FakeCollection()
        self.assertEqual(index_documents(collection, [("notes", "a note")]), 1)
        hits = retrieve(collection, "question")
        self.assertEqual(hits[0]["source"], "notes")
        self.assertEqual(
            format_context(hits), "[notes | retrieval distance: 0.120]\nretrieved text"
        )


if __name__ == "__main__":
    unittest.main()
