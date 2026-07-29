from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.ontology.schema_registry import OntologyRegistry
from src.db.models import IngestedRecord, QuarantineRecord, IngestionLog
from src.rag.rag_pipeline import RAGPipeline


class SkillExecutionResult(BaseModel):
    skill_name: str
    status: str
    output: Dict[str, Any]
    error: Optional[str] = None


class BaseAgentSkill(ABC):
    """Abstract base class for modular agent skills."""
    name: str
    description: str
    allowed_roles: List[str]

    @abstractmethod
    def execute(self, params: Dict[str, Any], db: Session, user_role: str = "analyst") -> SkillExecutionResult:
        pass


class Text2SQLQuerySkill(BaseAgentSkill):
    """Skill to execute structured SQL analytics queries using the Ontology Registry."""
    name = "text2sql_query"
    description = "Führt strukturierte Datenabfragen auf Geschäftskennzahlen basierend auf der Ontologie aus."
    allowed_roles = ["admin", "analyst", "reporting"]

    def __init__(self, ontology: OntologyRegistry = None):
        self.ontology = ontology or OntologyRegistry()

    def execute(self, params: Dict[str, Any], db: Session, user_role: str = "analyst") -> SkillExecutionResult:
        category = params.get("category")
        metric_name = params.get("metric_name")
        limit = params.get("limit", 50)

        query = db.query(IngestedRecord)
        if category:
            query = query.filter(IngestedRecord.category == category)
        if metric_name:
            query = query.filter(IngestedRecord.metric_name == metric_name)

        records = query.limit(limit).all()
        
        # Apply role-based filtering
        table_meta = self.ontology.get_table("ingested_records")
        results = []
        for r in records:
            rec_dict = {
                "id": r.id,
                "source_file": r.source_file,
                "entity_id": r.entity_id if user_role in ["admin", "analyst"] else "[RESTRICTED_BY_RBAC]",
                "metric_name": r.metric_name,
                "metric_value": r.metric_value,
                "category": r.category
            }
            results.append(rec_dict)

        return SkillExecutionResult(
            skill_name=self.name,
            status="SUCCESS",
            output={
                "record_count": len(results),
                "user_role": user_role,
                "records": results
            }
        )


class DocumentRAGSkill(BaseAgentSkill):
    """Skill to perform semantic RAG search across indexed documents."""
    name = "document_rag_search"
    description = "Sucht in unstrukturierten Dokumenten (Verträge, PDFs, Handbücher) und generiert Antworten via Qwen LLM."
    allowed_roles = ["admin", "analyst", "reporting"]

    def __init__(self, rag_pipeline: RAGPipeline = None):
        self.rag_pipeline = rag_pipeline or RAGPipeline()

    def execute(self, params: Dict[str, Any], db: Session, user_role: str = "analyst") -> SkillExecutionResult:
        question = params.get("question", "")
        top_k = params.get("top_k", 3)

        if not question:
            return SkillExecutionResult(
                skill_name=self.name,
                status="FAILED",
                output={},
                error="Parameter 'question' is required."
            )

        rag_res = self.rag_pipeline.query(question=question, top_k=top_k)
        return SkillExecutionResult(
            skill_name=self.name,
            status="SUCCESS",
            output=rag_res.model_dump()
        )


class DataHealthCheckSkill(BaseAgentSkill):
    """Skill to perform automated health checks on ingestion, quarantine rates, and database state."""
    name = "data_health_check"
    description = "Überprüft System-Gesundheit, Ingestion-Quoten und Quarantäne-Raten."
    allowed_roles = ["admin", "analyst"]

    def execute(self, params: Dict[str, Any], db: Session, user_role: str = "analyst") -> SkillExecutionResult:
        total_ingested = db.query(IngestedRecord).count()
        total_quarantined = db.query(QuarantineRecord).count()
        total_logs = db.query(IngestionLog).count()

        quarantine_rate = 0.0
        if (total_ingested + total_quarantined) > 0:
            quarantine_rate = round((total_quarantined / (total_ingested + total_quarantined)) * 100, 2)

        health_status = "HEALTHY" if quarantine_rate < 10.0 else "WARNING_HIGH_QUARANTINE"

        return SkillExecutionResult(
            skill_name=self.name,
            status="SUCCESS",
            output={
                "health_status": health_status,
                "total_ingested_records": total_ingested,
                "total_quarantined_records": total_quarantined,
                "total_batches_processed": total_logs,
                "quarantine_rate_percentage": quarantine_rate
            }
        )
