import os
import uuid
import time
import datetime
from sqlalchemy.orm import Session

from src.db.models import IngestedRecord, IngestionLog
from src.ingestion.csv_parser import CSVParserEngine
from src.ingestion.quarantine import QuarantineManager


class IngestionPipeline:
    """Orchestrates CSV file ingestion, validation, persistence, and auditing."""

    def __init__(self, parser: CSVParserEngine = None, quarantine_mgr: QuarantineManager = None):
        self.parser = parser or CSVParserEngine()
        self.quarantine_mgr = quarantine_mgr or QuarantineManager()

    def process_file(self, db: Session, file_path: str) -> IngestionLog:
        """Executes full ingestion pipeline on a single file."""
        start_time = time.time()
        filename = os.path.basename(file_path)
        batch_id = f"batch_{uuid.uuid4().hex[:12]}"
        
        log = IngestionLog(
            batch_id=batch_id,
            filename=filename,
            status="PROCESSING"
        )

        try:
            valid_rows, invalid_rows = self.parser.parse_and_validate(file_path)
            
            # Persist valid records in bulk
            db_records = []
            for row in valid_rows:
                rec = IngestedRecord(
                    source_file=filename,
                    record_batch_id=batch_id,
                    row_number=row["row_number"],
                    entity_id=str(row.get("entity_id")),
                    metric_name=str(row.get("metric_name", "unnamed")),
                    metric_value=row.get("metric_value"),
                    category=str(row.get("category", "default")),
                    raw_data=row
                )
                db_records.append(rec)

            if db_records:
                db.bulk_save_objects(db_records)

            # Persist quarantined rows
            if invalid_rows:
                self.quarantine_mgr.quarantine_rows(db, filename, invalid_rows)

            # Execution stats
            elapsed_ms = (time.time() - start_time) * 1000
            total = len(valid_rows) + len(invalid_rows)
            
            log.total_rows = total
            log.valid_rows = len(valid_rows)
            log.quarantined_rows = len(invalid_rows)
            log.status = "SUCCESS" if len(invalid_rows) == 0 else "PARTIAL_QUARANTINE"
            log.execution_time_ms = elapsed_ms
            
            db.add(log)
            db.commit()

        except Exception as e:
            # File-level failure -> Quarantine whole file
            db.rollback()
            elapsed_ms = (time.time() - start_time) * 1000
            
            quarantined_path = self.quarantine_mgr.quarantine_file(file_path, str(e))
            
            log.status = "FAILED"
            log.execution_time_ms = elapsed_ms
            log.total_rows = 0
            log.valid_rows = 0
            log.quarantined_rows = 0
            
            db.add(log)
            db.commit()

        return log
