import os
import shutil
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.database import Base
from src.db.models import IngestedRecord, QuarantineRecord, IngestionLog
from src.ingestion.csv_parser import CSVParserEngine
from src.ingestion.quarantine import QuarantineManager
from src.ingestion.pipeline import IngestionPipeline


@pytest.fixture
def test_db():
    """Creates isolated in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    yield db
    db.close()


@pytest.fixture
def tmp_dirs(tmp_path):
    """Creates temporary directories for testing files."""
    incoming = tmp_path / "incoming"
    quarantine = tmp_path / "quarantine"
    incoming.mkdir()
    quarantine.mkdir()
    return incoming, quarantine


def test_valid_csv_parsing(tmp_dirs, test_db):
    incoming_dir, quarantine_dir = tmp_dirs
    csv_file = incoming_dir / "valid_sales.csv"
    csv_file.write_text("entity_id,metric_name,metric_value,category\nCUST_001,revenue,150.50,electronics\nCUST_002,revenue,99.99,software\n")

    parser = CSVParserEngine()
    quarantine_mgr = QuarantineManager(quarantine_dir=str(quarantine_dir))
    pipeline = IngestionPipeline(parser=parser, quarantine_mgr=quarantine_mgr)

    log = pipeline.process_file(test_db, str(csv_file))

    assert log.status == "SUCCESS"
    assert log.total_rows == 2
    assert log.valid_rows == 2
    assert log.quarantined_rows == 0

    records = test_db.query(IngestedRecord).all()
    assert len(records) == 2
    assert records[0].entity_id == "CUST_001"
    assert records[0].metric_value == 150.50


def test_invalid_rows_quarantine(tmp_dirs, test_db):
    incoming_dir, quarantine_dir = tmp_dirs
    csv_file = incoming_dir / "mixed_sales.csv"
    # Row 2 is missing entity_id (invalid)
    csv_file.write_text("entity_id,metric_name,metric_value,category\nCUST_001,revenue,150.50,electronics\n,revenue,99.99,software\n")

    parser = CSVParserEngine()
    quarantine_mgr = QuarantineManager(quarantine_dir=str(quarantine_dir))
    pipeline = IngestionPipeline(parser=parser, quarantine_mgr=quarantine_mgr)

    log = pipeline.process_file(test_db, str(csv_file))

    assert log.status == "PARTIAL_QUARANTINE"
    assert log.valid_rows == 1
    assert log.quarantined_rows == 1

    valid_records = test_db.query(IngestedRecord).all()
    assert len(valid_records) == 1

    quarantined = test_db.query(QuarantineRecord).all()
    assert len(quarantined) == 1
    assert quarantined[0].row_number == 2
    assert "entity_id cannot be null" in quarantined[0].error_reason


def test_corrupted_file_quarantine(tmp_dirs, test_db):
    incoming_dir, quarantine_dir = tmp_dirs
    csv_file = incoming_dir / "corrupted.csv"
    # Completely invalid CSV structure (missing required columns)
    csv_file.write_text("wrong_col1,wrong_col2\nval1,val2\n")

    parser = CSVParserEngine()
    quarantine_mgr = QuarantineManager(quarantine_dir=str(quarantine_dir))
    pipeline = IngestionPipeline(parser=parser, quarantine_mgr=quarantine_mgr)

    log = pipeline.process_file(test_db, str(csv_file))

    assert log.status == "FAILED"
    assert log.valid_rows == 0

    # File should have been moved to quarantine directory
    quarantined_files = list(quarantine_dir.glob("*.csv"))
    assert len(quarantined_files) == 1
