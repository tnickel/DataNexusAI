import os
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from src.db.database import get_db
from src.db.models import IngestedRecord
from src.ontology.schema_registry import OntologyRegistry
from src.api.auth import get_current_agent, AgentUser
from src.api.rbac import RBACFilterEngine
from src.rag.rag_pipeline import RAGPipeline
from src.agents.router import AgentRouter

router = APIRouter(prefix="/api/v1", tags=["DataNexus Data-Access Layer"])
ontology_registry = OntologyRegistry()
rbac_engine = RBACFilterEngine(ontology_registry)
rag_pipeline = RAGPipeline()
agent_router = AgentRouter()


class StructuredQueryRequest(BaseModel):
    category: Optional[str] = None
    metric_name: Optional[str] = None
    limit: int = 100


class IndexDocumentRequest(BaseModel):
    doc_id: str
    title: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RAGQueryRequest(BaseModel):
    question: str
    top_k: int = 3


class AgentExecuteRequest(BaseModel):
    skill_name: str
    params: Dict[str, Any] = Field(default_factory=dict)


@router.get("/ontology/schemas")
def get_ontology_schemas(agent: AgentUser = Depends(get_current_agent)):
    """
    Returns the semantic ontology schema descriptions and formatted system prompt
    tailored to the agent's RBAC role for LLM Text2SQL prompts.
    """
    system_prompt = ontology_registry.generate_llm_system_prompt(user_role=agent.role)
    tables = [t.model_dump() for t in ontology_registry.list_tables()]
    return {
        "agent_role": agent.role,
        "system_prompt": system_prompt,
        "tables": tables
    }


@router.get("/data/records")
def get_data_records(
    category: Optional[str] = Query(None, description="Filter by business category"),
    metric_name: Optional[str] = Query(None, description="Filter by KPI metric name"),
    limit: int = Query(50, ge=1, le=1000),
    db: Session = Depends(get_db),
    agent: AgentUser = Depends(get_current_agent)
):
    """
    Queries ingested records from database and applies RBAC column-level filtering
    and PII masking based on the agent's authenticated role.
    """
    query = db.query(IngestedRecord)
    if category:
        query = query.filter(IngestedRecord.category == category)
    if metric_name:
        query = query.filter(IngestedRecord.metric_name == metric_name)

    records = query.limit(limit).all()
    
    # Convert ORM records to dicts
    raw_dicts = []
    for r in records:
        raw_dicts.append({
            "id": r.id,
            "source_file": r.source_file,
            "entity_id": r.entity_id,
            "metric_name": r.metric_name,
            "metric_value": r.metric_value,
            "category": r.category,
            "created_at": r.created_at.isoformat() if r.created_at else None
        })

    # Apply RBAC Filter Engine
    filtered_records = rbac_engine.filter_records_list("ingested_records", raw_dicts, agent)

    return {
        "count": len(filtered_records),
        "agent_role": agent.role,
        "records": filtered_records
    }


@router.post("/data/query")
def execute_structured_query(
    body: StructuredQueryRequest,
    db: Session = Depends(get_db),
    agent: AgentUser = Depends(get_current_agent)
):
    """Structured query endpoint proxy for KI Agents."""
    return get_data_records(
        category=body.category,
        metric_name=body.metric_name,
        limit=body.limit,
        db=db,
        agent=agent
    )


# --- Stage 3: RAG Endpoints ---

@router.post("/rag/index_document")
def index_document_endpoint(
    body: IndexDocumentRequest,
    agent: AgentUser = Depends(get_current_agent)
):
    """Indexes a text document into the Milvus / Vector Store for RAG search."""
    chunk_count = rag_pipeline.index_document(
        doc_id=body.doc_id,
        title=body.title,
        content=body.content,
        metadata=body.metadata
    )
    return {
        "status": "SUCCESS",
        "doc_id": body.doc_id,
        "title": body.title,
        "indexed_chunks": chunk_count
    }


@router.post("/rag/query")
def rag_query_endpoint(
    body: RAGQueryRequest,
    agent: AgentUser = Depends(get_current_agent)
):
    """Performs RAG search against Milvus Vector Store & generates local Qwen LLM answer."""
    response = rag_pipeline.query(question=body.question, top_k=body.top_k)
    return response.model_dump()


# --- Stage 4: Agentic Framework & Skills Endpoints ---

@router.get("/agent/skills")
def list_agent_skills(agent: AgentUser = Depends(get_current_agent)):
    """Lists available agent skills tailored to agent's RBAC role."""
    skills = agent_router.list_skills(user_role=agent.role)
    return {
        "agent_role": agent.role,
        "available_skills": skills
    }


@router.post("/agent/execute")
def execute_agent_skill(
    body: AgentExecuteRequest,
    db: Session = Depends(get_db),
    agent: AgentUser = Depends(get_current_agent)
):
    """Executes a modular agent skill using static route dispatching."""
    result = agent_router.route_and_execute(
        skill_name=body.skill_name,
        params=body.params,
        db=db,
        user_role=agent.role
    )
    if result.status == "FORBIDDEN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result.error
        )
    if result.status == "FAILED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error
        )
        
    return result.model_dump()


# --- Documentation Viewer Endpoints ---

@router.get("/docs/handbuch", response_class=PlainTextResponse)
def get_betriebshandbuch():
    path = os.path.join("docs", "BETRIEBSHANDBUCH.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return "Betriebshandbuch nicht gefunden."


@router.get("/docs/fortschritt", response_class=PlainTextResponse)
def get_fortschrittsbericht():
    path = os.path.join("docs", "FORTSCHRITT.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return "Fortschrittsbericht nicht gefunden."
