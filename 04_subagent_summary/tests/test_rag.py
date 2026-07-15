import unittest
from pathlib import Path
from rag import load_documents,chunk_text,index_documents,retrieve
class F:
 def upsert(s,**k):s.k=k
 def query(s,**k):return {'documents':[['x']],'metadatas':[[{'source':'n'}]],'distances':[[.1]]}
class T(unittest.TestCase):
 def test_rag(self):self.assertTrue(load_documents(Path(__file__).parents[1]/'documents'));self.assertEqual(chunk_text('a\n\nb',10),['a\n\nb']);c=F();self.assertEqual(index_documents(c,[('n','x')]),1);self.assertEqual(retrieve(c,'q')[0]['source'],'n')
if __name__=='__main__':unittest.main()
