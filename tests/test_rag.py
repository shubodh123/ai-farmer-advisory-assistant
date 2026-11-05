"""
Unit tests for RAG components: DocumentStore, Chunker, and AgriculturalRetriever.
"""
import unittest
from rag.document_store import DocumentStore
from rag.retriever import AgriculturalRetriever

class TestRAGPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = DocumentStore()
        cls.retriever = AgriculturalRetriever(cls.store)

    def test_store_loaded_documents(self):
        self.assertGreater(self.store.total_docs, 5, "Knowledge base should contain at least 5 chunks")

    def test_wheat_retrieval(self):
        results = self.retriever.retrieve("What is the seed rate for wheat?", top_k=2)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["crop"], "Wheat")

    def test_paddy_blast_retrieval(self):
        results = self.retriever.retrieve("blast disease in rice tricyclazole", top_k=2)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["crop"], "Rice/Paddy")

    def test_hindi_query_expansion(self):
        expanded = self.retriever.expand_query("गेहूं में पीली कुंगी")
        self.assertIn("wheat", expanded)
        self.assertIn("yellow rust", expanded)

if __name__ == "__main__":
    unittest.main()
