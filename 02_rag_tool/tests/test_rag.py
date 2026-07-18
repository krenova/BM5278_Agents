import unittest
from pathlib import Path

from rag import chunk_text, format_context, index_documents, load_documents, retrieve


class Fake:
    def upsert(self, **kw):
        self.data = kw

    def query(self, **kw):
        return {"documents": [["x"]], "metadatas": [[{"source": "n"}]], "distances": [[0.1]]}


class TestRag(unittest.TestCase):
    def test_load(self):
        self.assertTrue(load_documents(Path(__file__).parents[1] / "documents"))
        self.assertEqual(chunk_text("a\n\nb", 10), ["a\n\nb"])

    def test_index_retrieve(self):
        c = Fake()
        self.assertEqual(index_documents(c, [("n", "x")]), 1)
        hits = retrieve(c, "q")
        self.assertEqual(hits[0]["source"], "n")
        self.assertEqual(format_context(hits), "[n | retrieval distance: 0.100]\nx")


if __name__ == "__main__":
    unittest.main()
