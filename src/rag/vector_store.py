import math
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    chunk_id: str
    doc_id: str
    title: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None


class SearchResult(BaseModel):
    chunk: DocumentChunk
    similarity_score: float


class VectorStore:
    """
    Vector Store implementation for Milvus / Local In-Memory Vector Search.
    Computes Cosine Similarity for semantic document retrieval.
    """

    def __init__(self, collection_name: str = "datanexus_knowledge"):
        self.collection_name = collection_name
        self.chunks: Dict[str, DocumentChunk] = {}

    def insert_chunk(self, chunk: DocumentChunk):
        self.chunks[chunk.chunk_id] = chunk

    def insert_chunks(self, chunks: List[DocumentChunk]):
        for c in chunks:
            self.insert_chunk(c)

    def _cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    def similarity_search(self, query_vector: List[float], top_k: int = 3) -> List[SearchResult]:
        """Performs Cosine Similarity search and returns top-K nearest document chunks."""
        results = []
        for chunk in self.chunks.values():
            if chunk.embedding:
                score = self._cosine_similarity(query_vector, chunk.embedding)
                results.append(SearchResult(chunk=chunk, similarity_score=score))

        # Sort by similarity score descending
        results.sort(key=lambda r: r.similarity_score, reverse=True)
        return results[:top_k]
