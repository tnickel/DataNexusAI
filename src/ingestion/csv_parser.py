import os
import polars as pl
import pandas as pd
from typing import Tuple, List, Dict, Any


class CSVParserEngine:
    """High-performance Polars/Pandas CSV Parser and Validator."""

    def __init__(self, required_columns: List[str] = None):
        self.required_columns = required_columns or ["entity_id", "metric_name", "metric_value"]

    def parse_and_validate(self, file_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Parses CSV file using Polars.
        Returns tuple of (valid_records, invalid_records).
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV File not found: {file_path}")

        valid_records = []
        invalid_records = []

        try:
            # High-speed Polars CSV reading
            df = pl.read_csv(file_path, ignore_errors=True)
            
            # Normalize column names (lowercase, strip whitespace)
            df = df.rename({col: col.strip().lower() for col in df.columns})
            
            # Check required columns presence
            missing = [col for col in self.required_columns if col not in df.columns]
            if missing:
                raise ValueError(f"Missing required CSV columns: {missing}")

            # Process row by row for validation
            for i, row in enumerate(df.to_dicts(), start=1):
                is_valid = True
                reason = ""
                
                # Check entity_id non-null
                entity_id = row.get("entity_id")
                if not entity_id or str(entity_id).strip() == "" or str(entity_id) == "None":
                    is_valid = False
                    reason = "entity_id cannot be null or empty"
                
                # Check metric_value numeric
                metric_value = row.get("metric_value")
                try:
                    val = float(metric_value) if metric_value is not None else None
                    row["metric_value"] = val
                except (ValueError, TypeError):
                    is_valid = False
                    reason = f"Invalid numeric metric_value: {metric_value}"

                if is_valid:
                    row["row_number"] = i
                    valid_records.append(row)
                else:
                    invalid_records.append({
                        "row_number": i,
                        "reason": reason,
                        "raw_data": row
                    })

        except Exception as e:
            # Fallback parsing error
            raise ValueError(f"Failed to parse CSV file '{os.path.basename(file_path)}': {str(e)}")

        return valid_records, invalid_records
