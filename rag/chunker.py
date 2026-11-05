"""
Chunker module: splits agricultural advisory articles into semantically dense chunks
while preserving document metadata and source attribution.
"""
from typing import List, Dict, Any
import re

class DocumentChunker:
    def __init__(self, chunk_size: int = 350, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(self, doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        text = doc.get("content", "")
        doc_id = doc.get("id", "doc")
        crop = doc.get("crop", "General")
        category = doc.get("category", "Advisory")
        title = doc.get("title", "")
        source = doc.get("source", "ICAR/KVK Advisory")
        keywords = doc.get("keywords", [])

        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = []
        current_len = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            words = sentence.split()
            sentence_word_count = len(words)

            if current_len + sentence_word_count > self.chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append({
                    "chunk_id": f"{doc_id}-c{len(chunks)+1}",
                    "parent_id": doc_id,
                    "crop": crop,
                    "category": category,
                    "title": title,
                    "source": source,
                    "keywords": keywords,
                    "text": chunk_text
                })
                # Overlap: keep last sentence if applicable
                current_chunk = [current_chunk[-1]] if len(current_chunk) > 1 else []
                current_len = sum(len(s.split()) for s in current_chunk)

            current_chunk.append(sentence)
            current_len += sentence_word_count

        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append({
                "chunk_id": f"{doc_id}-c{len(chunks)+1}",
                "parent_id": doc_id,
                "crop": crop,
                "category": category,
                "title": title,
                "source": source,
                "keywords": keywords,
                "text": chunk_text
            })

        return chunks
