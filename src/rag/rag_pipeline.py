from typing import List, Dict, Any
from pydantic import BaseModel, Field

from src.rag.embeddings import EmbeddingEngine
from src.rag.vector_store import VectorStore, SearchResult
from src.rag.document_processor import DocumentProcessor
from src.rag.llm_client import LocalQwenLLMClient


class RAGResponse(BaseModel):
    query: str
    answer: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)


class RAGPipeline:
    """End-to-End RAG Engine combining Vector Store Search & Qwen LLM Inferenz."""

    def __init__(
        self,
        embedding_engine: EmbeddingEngine = None,
        vector_store: VectorStore = None,
        llm_client: LocalQwenLLMClient = None
    ):
        self.embedding_engine = embedding_engine or EmbeddingEngine()
        self.vector_store = vector_store or VectorStore()
        self.doc_processor = DocumentProcessor(self.embedding_engine, self.vector_store)
        self.llm_client = llm_client or LocalQwenLLMClient()

    def index_document(self, doc_id: str, title: str, content: str, metadata: Dict[str, Any] = None) -> int:
        """Chunks and indexes a text document into the Vector Store."""
        chunks = self.doc_processor.process_and_index_text(doc_id, title, content, metadata=metadata)
        return len(chunks)

    def query(self, question: str, top_k: int = 3) -> RAGResponse:
        """Performs RAG pipeline search and generates Qwen LLM answer."""
        query_vector = self.embedding_engine.embed_text(question)
        search_results: List[SearchResult] = self.vector_store.similarity_search(query_vector, top_k=top_k)

        retrieved_contexts = [r.chunk.content for r in search_results]
        sources = [
            {
                "doc_id": r.chunk.doc_id,
                "title": r.chunk.title,
                "similarity_score": round(r.similarity_score, 4),
                "snippet": r.chunk.content[:100] + "..."
            }
            for r in search_results
        ]

        answer = self.llm_client.generate_rag_response(question, retrieved_contexts)

        return RAGResponse(
            query=question,
            answer=answer,
            sources=sources
        )
