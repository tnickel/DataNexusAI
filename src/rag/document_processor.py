import uuid
from typing import List, Dict, Any
from src.rag.embeddings import EmbeddingEngine
from src.rag.vector_store import VectorStore, DocumentChunk


class DocumentProcessor:
    """Chunks documents into semantic segments and embeds them into VectorStore."""

    def __init__(self, embedding_engine: EmbeddingEngine = None, vector_store: VectorStore = None):
        self.embedding_engine = embedding_engine or EmbeddingEngine()
        self.vector_store = vector_store or VectorStore()

    def process_and_index_text(
        self,
        doc_id: str,
        title: str,
        text_content: str,
        chunk_size: int = 300,
        chunk_overlap: int = 50,
        metadata: Dict[str, Any] = None
    ) -> List[DocumentChunk]:
        """
        Splits text content into overlapping chunks, generates embeddings,
        and adds chunks to the vector store.
        """
        metadata = metadata or {}
        words = text_content.split()
        chunks = []
        
        step = chunk_size - chunk_overlap if chunk_size > chunk_overlap else chunk_size
        
        i = 0
        chunk_index = 0
        while i < len(words):
            chunk_words = words[i:i + chunk_size]
            chunk_text = " ".join(chunk_words)
            chunk_id = f"{doc_id}_chunk_{chunk_index}"
            
            embedding = self.embedding_engine.embed_text(chunk_text)
            
            chunk = DocumentChunk(
                chunk_id=chunk_id,
                doc_id=doc_id,
                title=title,
                content=chunk_text,
                metadata={**metadata, "chunk_index": chunk_index},
                embedding=embedding
            )
            
            chunks.append(chunk)
            self.vector_store.insert_chunk(chunk)
            
            chunk_index += 1
            i += step
            if i >= len(words) and len(chunks) == 0:
                break
                
        return chunks
