import unittest
from pathlib import Path

from rag import chunk_text, format_context, index_documents, load_documents, retrieve


class F:
    def upsert(s, **k):
        s.k = k

    def query(s, **k):
        return {"documents": [["x"]], "metadatas": [[{"source": "n"}]], "distances": [[0.1]]}


class T(unittest.TestCase):
    def test_rag(self):
        self.assertTrue(load_documents(Path(__file__).parents[1] / "documents"))
        self.assertEqual(chunk_text("a\n\nb", 10), ["a\n\nb"])
        c = F()
        self.assertEqual(index_documents(c, [("n", "x")]), 1)
        hits = retrieve(c, "q")
        self.assertEqual(hits[0]["source"], "n")
        self.assertEqual(format_context(hits), "[n | retrieval distance: 0.100]\nx")


if __name__ == "__main__":
    unittest.main()
