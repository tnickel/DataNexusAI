import os
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from src.db.database import SessionLocal, init_db
from src.ingestion.pipeline import IngestionPipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class CSVIncomingWatchdogHandler(FileSystemEventHandler):
    """Monitors incoming directory for new CSV uploads."""

    def __init__(self, pipeline: IngestionPipeline = None):
        self.pipeline = pipeline or IngestionPipeline()
        init_db()

    def on_created(self, event):
        if event.is_directory:
            return
        
        file_path = event.src_path
        if file_path.endswith(".csv"):
            logging.info(f"[Watchdog] New file detected: {file_path}")
            # Brief delay to allow file copy to finish
            time.sleep(0.5)
            
            db = SessionLocal()
            try:
                log = self.pipeline.process_file(db, file_path)
                logging.info(f"[Watchdog] Ingestion completed: {log.filename} (Status: {log.status}, Valid: {log.valid_rows}, Quarantined: {log.quarantined_rows})")
            except Exception as e:
                logging.error(f"[Watchdog] Ingestion failed for {file_path}: {e}")
            finally:
                db.close()


def start_directory_watchdog(watch_dir: str = "./incoming"):
    """Starts directory watchdog process."""
    os.makedirs(watch_dir, exist_ok=True)
    event_handler = CSVIncomingWatchdogHandler()
    observer = Observer()
    observer.schedule(event_handler, path=watch_dir, recursive=False)
    observer.start()
    logging.info(f"[Watchdog] Started monitoring directory: {watch_dir}")
    return observer
