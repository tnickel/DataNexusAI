import pytest

from src.rag.embeddings import EmbeddingEngine
from src.rag.vector_store import VectorStore, DocumentChunk
from src.rag.document_processor import DocumentProcessor
from src.rag.llm_client import LocalQwenLLMClient
from src.rag.rag_pipeline import RAGPipeline


def test_embedding_engine():
    engine = EmbeddingEngine(vector_dim=64)
    vec = engine.embed_text("DataNexus AI Enterprise Pipeline")
    assert len(vec) == 64
    # Check L2 normalization
    norm = sum(x * x for x in vec)
    assert abs(norm - 1.0) < 1e-4


def test_vector_store_similarity_search():
    store = VectorStore()
    chunk1 = DocumentChunk(
        chunk_id="chunk_1",
        doc_id="doc_001",
        title="Vertrag A",
        content="Die Kündigungsfrist beträgt 3 Monate zum Quartalsende.",
        embedding=[1.0, 0.0, 0.0]
    )
    chunk2 = DocumentChunk(
        chunk_id="chunk_2",
        doc_id="doc_002",
        title="Handbuch B",
        content="Der Server läuft im Telekom Cloud Rechenzentrum Frankfurt.",
        embedding=[0.0, 1.0, 0.0]
    )
    store.insert_chunks([chunk1, chunk2])

    results = store.similarity_search([0.9, 0.1, 0.0], top_k=1)
    assert len(results) == 1
    assert results[0].chunk.chunk_id == "chunk_1"
    assert results[0].similarity_score > 0.8


def test_document_processor_chunking():
    engine = EmbeddingEngine(vector_dim=32)
    store = VectorStore()
    processor = DocumentProcessor(embedding_engine=engine, vector_store=store)

    text = "Wort1 Wort2 Wort3 Wort4 Wort5 Wort6 Wort7 Wort8 Wort9 Wort10 Wort11 Wort12"
    chunks = processor.process_and_index_text(
        doc_id="doc_test",
        title="Test Doku",
        text_content=text,
        chunk_size=5,
        chunk_overlap=2
    )

    assert len(chunks) > 1
    assert chunks[0].doc_id == "doc_test"
    assert len(store.chunks) == len(chunks)


def test_llm_client_response():
    client_llm = LocalQwenLLMClient()
    response = client_llm.generate_rag_response(
        user_query="Wo steht der Server?",
        retrieved_contexts=["Der Server steht in der Open Telekom Cloud in Frankfurt."]
    )
    assert "Open Telekom Cloud" in response or "Lokale Qwen" in response


def test_rag_pipeline_end_to_end():
    pipeline = RAGPipeline()
    chunk_count = pipeline.index_document(
        doc_id="contract_2026",
        title="Service Level Agreement",
        content="Die maximale Latenz der Ingestion Pipeline beträgt 500 Millisekunden."
    )
    assert chunk_count >= 1

    res = pipeline.query("Wie hoch ist die maximale Latenz?")
    assert res.query == "Wie hoch ist die maximale Latenz?"
    assert len(res.sources) >= 1
    assert res.sources[0]["doc_id"] == "contract_2026"


def test_fastapi_rag_endpoints(api_client):
    # Index document via API
    index_res = api_client.post(
        "/api/v1/rag/index_document",
        json={
            "doc_id": "api_doc_100",
            "title": "Datenschutz Richtlinie",
            "content": "Alle personenbezogenen Daten werden nach DSGVO im deutschen Rechenzentrum verarbeitet.",
            "metadata": {"author": "Datenschutzbeauftragter"}
        },
        headers={"X-API-Key": "key_analyst_secret_456"}
    )
    assert index_res.status_code == 200
    assert index_res.json()["status"] == "SUCCESS"
    assert index_res.json()["indexed_chunks"] >= 1

    # Query RAG via API
    query_res = api_client.post(
        "/api/v1/rag/query",
        json={
            "question": "Welche Datenschutzregeln gelten?",
            "top_k": 2
        },
        headers={"X-API-Key": "key_analyst_secret_456"}
    )
    assert query_res.status_code == 200
    data = query_res.json()
    assert "answer" in data
    assert len(data["sources"]) >= 1
