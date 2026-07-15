import unittest
from pathlib import Path
from rag import load_documents,chunk_text,index_documents,retrieve
class F:
 def upsert(s,**kw):s.kw=kw
 def query(s,**kw):return {'documents':[['x']],'metadatas':[[{'source':'n'}]],'distances':[[.2]]}
class T(unittest.TestCase):
 def test_load(self):self.assertTrue(load_documents(Path(__file__).parents[1]/'documents'));self.assertEqual(chunk_text('a\n\nb',10),['a\n\nb'])
 def test_index(self):c=F();self.assertEqual(index_documents(c,[('n','x')]),1);self.assertEqual(retrieve(c,'?')[0]['source'],'n')
if __name__=='__main__':unittest.main()
