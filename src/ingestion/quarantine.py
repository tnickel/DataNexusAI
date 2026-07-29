import os
import shutil
import datetime
from sqlalchemy.orm import Session
from src.db.models import QuarantineRecord, IngestionLog


class QuarantineManager:
    """Manages invalid files and corrupted rows."""

    def __init__(self, quarantine_dir: str = "./quarantine"):
        self.quarantine_dir = quarantine_dir
        os.makedirs(self.quarantine_dir, exist_ok=True)

    def quarantine_file(self, file_path: str, reason: str) -> str:
        """Moves a completely corrupted or unparseable file to quarantine directory."""
        if not os.path.exists(file_path):
            return ""
        
        filename = os.path.basename(file_path)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        target_path = os.path.join(self.quarantine_dir, f"{timestamp}_{filename}")
        
        shutil.move(file_path, target_path)
        
        # Write metadata sidecar file
        meta_path = f"{target_path}.reason.txt"
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(f"Quarantined At: {datetime.datetime.now().isoformat()}\nReason: {reason}\n")
            
        return target_path

    def quarantine_rows(self, db: Session, filename: str, invalid_rows: list[dict]):
        """Persists individual invalid rows into QuarantineRecord table."""
        records = []
        for row in invalid_rows:
            rec = QuarantineRecord(
                source_file=filename,
                row_number=row.get("row_number", -1),
                error_reason=row.get("reason", "Validation failure"),
                raw_row_content=str(row.get("raw_data", ""))
            )
            records.append(rec)
            
        if records:
            db.bulk_save_objects(records)
            db.commit()
