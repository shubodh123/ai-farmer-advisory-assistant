"""
Hybrid In-Memory Document Store: Sparse BM25-style indexing + Dense TF-IDF vector representations.
Zero external heavy dependencies required, while fully compliant with RAG requirements.
"""
import os
import json
import glob
import math
import re
from typing import List, Dict, Any, Tuple
from rag.chunker import DocumentChunker

STOPWORDS = {
    "what", "is", "the", "of", "and", "in", "to", "for", "on", "at", "with", "a", "an",
    "this", "that", "it", "are", "be", "as", "by", "from", "or", "how", "can", "today",
    "yesterday", "me", "my", "your", "tell", "show", "give", "do", "does", "did", "so"
}

class DocumentStore:
    def __init__(self, kb_dir: str = None):
        if kb_dir is None:
            kb_dir = os.path.join(os.path.dirname(__file__), "knowledge_base")
        self.kb_dir = kb_dir
        self.chunker = DocumentChunker()
        self.chunks: List[Dict[str, Any]] = []
        self.doc_freq: Dict[str, int] = {}
        self.chunk_vectors: List[Dict[str, float]] = []
        self.vocabulary: set = set()
        self.total_docs: int = 0
        self.avg_doc_len: float = 0.0
        self.load_and_index()

    def _tokenize(self, text: str) -> List[str]:
        cleaned = re.sub(r'[^a-zA-Z0-9\u0900-\u097F\u0A00-\u0A7F\u0C00-\u0C7F\u0B80-\u0BFF\s]', ' ', text.lower())
        tokens = [t.strip() for t in cleaned.split() if len(t.strip()) > 1 and t.strip() not in STOPWORDS]
        return tokens

    def load_and_index(self):
        json_files = glob.glob(os.path.join(self.kb_dir, "*.json"))
        raw_documents = []
        for file_path in json_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    docs = json.load(f)
                    if isinstance(docs, list):
                        raw_documents.extend(docs)
                    elif isinstance(docs, dict):
                        raw_documents.append(docs)
            except Exception as e:
                print(f"[Warning] Failed to load {file_path}: {e}")

        self.chunks = []
        for doc in raw_documents:
            self.chunks.extend(self.chunker.chunk_document(doc))

        self.total_docs = len(self.chunks)
        if self.total_docs == 0:
            return

        total_tokens = 0
        self.doc_freq = {}
        tokenized_chunks = []

        for chunk in self.chunks:
            full_text = f"{chunk['title']} {chunk['crop']} {chunk['category']} {chunk['text']} {' '.join(chunk.get('keywords', []))}"
            tokens = self._tokenize(full_text)
            tokenized_chunks.append(tokens)
            total_tokens += len(tokens)
            unique_tokens = set(tokens)
            for t in unique_tokens:
                self.doc_freq[t] = self.doc_freq.get(t, 0) + 1
            self.vocabulary.update(unique_tokens)

        self.avg_doc_len = total_tokens / max(1, self.total_docs)

        # Build TF-IDF vectors for dense/hybrid search
        self.chunk_vectors = []
        for tokens in tokenized_chunks:
            tf: Dict[str, float] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            vec: Dict[str, float] = {}
            norm = 0.0
            for t, count in tf.items():
                idf = math.log((self.total_docs + 1) / (self.doc_freq.get(t, 0) + 1)) + 1.0
                val = count * idf
                vec[t] = val
                norm += val * val
            norm = math.sqrt(norm) if norm > 0 else 1.0
            for t in vec:
                vec[t] /= norm
            self.chunk_vectors.append(vec)

    def bm25_score(self, query_tokens: List[str], chunk_idx: int, k1: float = 1.5, b: float = 0.75) -> float:
        chunk = self.chunks[chunk_idx]
        full_text = f"{chunk['title']} {chunk['crop']} {chunk['category']} {chunk['text']} {' '.join(chunk.get('keywords', []))}"
        tokens = self._tokenize(full_text)
        doc_len = len(tokens)
        score = 0.0
        token_counts = {}
        for t in tokens:
            token_counts[t] = token_counts.get(t, 0) + 1

        for qt in query_tokens:
            if qt not in self.doc_freq:
                continue
            df = self.doc_freq[qt]
            idf = math.log((self.total_docs - df + 0.5) / (df + 0.5) + 1.0)
            tf = token_counts.get(qt, 0)
            numerator = tf * (k1 + 1.0)
            denominator = tf + k1 * (1.0 - b + b * (doc_len / max(1.0, self.avg_doc_len)))
            score += idf * (numerator / max(0.001, denominator))
        return score

    def vector_score(self, query_tokens: List[str], chunk_idx: int) -> float:
        query_tf: Dict[str, float] = {}
        for t in query_tokens:
            query_tf[t] = query_tf.get(t, 0) + 1
        q_vec = {}
        norm = 0.0
        for t, count in query_tf.items():
            idf = math.log((self.total_docs + 1) / (self.doc_freq.get(t, 0) + 1)) + 1.0
            val = count * idf
            q_vec[t] = val
            norm += val * val
        norm = math.sqrt(norm) if norm > 0 else 1.0
        for t in q_vec:
            q_vec[t] /= norm

        c_vec = self.chunk_vectors[chunk_idx]
        dot_product = sum(q_vec[t] * c_vec[t] for t in q_vec if t in c_vec)
        return dot_product

    def search(self, query: str, top_k: int = 3, alpha: float = 0.5) -> List[Tuple[Dict[str, Any], float]]:
        """
        Hybrid search combining BM25 score and TF-IDF Cosine Vector similarity.
        alpha = weight for dense vector similarity (0.0 = pure BM25, 1.0 = pure vector)
        """
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        bm25_scores = [self.bm25_score(query_tokens, i) for i in range(self.total_docs)]
        max_bm25 = max(bm25_scores) if bm25_scores and max(bm25_scores) > 0 else 1.0

        scored_results = []
        for i in range(self.total_docs):
            norm_bm25 = bm25_scores[i] / max_bm25
            v_score = self.vector_score(query_tokens, i)
            hybrid_score = (1.0 - alpha) * norm_bm25 + alpha * v_score
            if hybrid_score > 0.05:
                scored_results.append((self.chunks[i], hybrid_score))

        scored_results.sort(key=lambda x: x[1], reverse=True)
        return scored_results[:top_k]
