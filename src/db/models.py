import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from src.db.database import Base


class IngestedRecord(Base):
    """Stores validated ingested records from CSV imports."""
    __tablename__ = "ingested_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    source_file = Column(String(255), nullable=False, index=True)
    record_batch_id = Column(String(64), nullable=False, index=True)
    row_number = Column(Integer, nullable=False)
    
    # Generic payload fields (can adapt to domain schema)
    entity_id = Column(String(100), nullable=True, index=True)
    metric_name = Column(String(100), nullable=True, index=True)
    metric_value = Column(Float, nullable=True)
    category = Column(String(100), nullable=True, index=True)
    raw_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class QuarantineRecord(Base):
    """Stores invalid or corrupted CSV rows that failed schema validation."""
    __tablename__ = "quarantine_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    source_file = Column(String(255), nullable=False, index=True)
    row_number = Column(Integer, nullable=False)
    error_reason = Column(Text, nullable=False)
    raw_row_content = Column(Text, nullable=False)
    quarantined_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class IngestionLog(Base):
    """Audit log for ingestion batch executions."""
    __tablename__ = "ingestion_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    batch_id = Column(String(64), nullable=False, unique=True, index=True)
    filename = Column(String(255), nullable=False)
    total_rows = Column(Integer, default=0)
    valid_rows = Column(Integer, default=0)
    quarantined_rows = Column(Integer, default=0)
    status = Column(String(50), nullable=False, default="SUCCESS")  # SUCCESS, FAILED, PARTIAL_QUARANTINE
    execution_time_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
