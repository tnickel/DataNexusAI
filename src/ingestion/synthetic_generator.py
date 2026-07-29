import os
import random
import uuid
import datetime
import pandas as pd
from typing import List, Dict, Tuple


class SyntheticDataGenerator:
    """
    Synthetic Data & Document Generator for testing DataNexus AI Ingestion & RAG Pipelines.
    """

    CATEGORIES = ["FINANCE", "TELECOM", "INFRASTRUCTURE", "SECURITY", "CUSTOMER_OPS"]
    METRICS = {
        "FINANCE": ["MONTHLY_REVENUE_EUR", "OPERATING_COST_EUR", "PROFIT_MARGIN_PCT"],
        "TELECOM": ["DATA_THROUGHPUT_GBPS", "LATENCY_MS", "ACTIVE_5G_CONNECTIONS"],
        "INFRASTRUCTURE": ["CPU_UTILIZATION_PCT", "RAM_USAGE_GB", "STORAGE_FREE_TB"],
        "SECURITY": ["FAILED_LOGIN_ATTEMPTS", "SSL_CERT_EXPIRY_DAYS", "FIREWALL_BLOCKED_IPS"],
        "CUSTOMER_OPS": ["ACTIVE_TICKETS", "AVG_RESPONSE_TIME_MIN", "CUSTOMER_SATISFACTION_SCORE"]
    }

    RAG_TEMPLATES = [
        ("SLA Vertrag - OTC Cloud Service Level Agreement {year}", 
         "Die DataNexus AI Plattform garantiert im Rechenzentrum Frankfurt eine Verfügbarkeit von {sla_pct}%. "
         "Sollte die Ausfallzeit in einem Monat {max_downtime} Minuten überschreiten, greift die Gutschriftvereinbarung nach §4 Abs. 2. "
         "Ansprechpartner für technische Notfälle ist das Security Operations Center unter SOC-HOTLINE-{soc_id}."),
        
        ("Betriebsanleitung - Data Ingestion Pipeline & Watchdog {code}", 
         "Der Ingestion Watchdog überwacht kontinuierlich den Ordner 'incoming/'. "
         "Dateien werden mit der Polars Engine in unter {speed_ms} ms geparst. "
         "Fehlerhafte Zeilen werden automatisch in die Quarantäne isoliert (Dead-Letter Queue). "
         "Batch-ID für diesen Vorgang: BATCH-{batch_uuid}."),
        
        ("Sicherheitskonzept - RBAC & PII Anonymisierung Version {version}", 
         "Sämtliche personenbezogenen Daten (PII) wie Kundennummern und Adressen werden für nicht-autorisierte Rollen "
         "(Reporting Agent) automatisch durch den String '[RESTRICTED_BY_RBAC]' ersetzt. "
         "Die Identitätsprüfung erfolgt via X-API-Key Header mit Sha256 Hashing. Sicherheitsaudit am {audit_date}.")
    ]

    @classmethod
    def generate_csv_file(
        cls,
        output_path: str,
        num_records: int = 50,
        include_quarantine_errors: bool = True
    ) -> Tuple[str, int, int]:
        """
        Generates a synthetic CSV file with structured metric records.
        Optionally injects edge-case quarantine errors for testing.
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        rows = []
        valid_cnt = 0
        quar_cnt = 0

        for i in range(1, num_records + 1):
            category = random.choice(cls.CATEGORIES)
            metric_name = random.choice(cls.METRICS[category])
            
            # 10% chance to inject an intentional quarantine error if enabled
            if include_quarantine_errors and (i % 10 == 0):
                quar_cnt += 1
                error_type = random.choice(["missing_entity", "invalid_metric_val", "missing_metric_name"])
                if error_type == "missing_entity":
                    rows.append({
                        "entity_id": "",  # Empty mandatory entity ID
                        "metric_name": metric_name,
                        "metric_value": round(random.uniform(10.0, 5000.0), 2),
                        "category": category
                    })
                elif error_type == "invalid_metric_val":
                    rows.append({
                        "entity_id": f"CUST_{1000 + i}",
                        "metric_name": metric_name,
                        "metric_value": "CORRUPTED_VALUE_STRING",  # Corrupted string instead of float
                        "category": category
                    })
                else:
                    rows.append({
                        "entity_id": f"CUST_{1000 + i}",
                        "metric_name": "",  # Missing metric name
                        "metric_value": round(random.uniform(10.0, 5000.0), 2),
                        "category": category
                    })
            else:
                valid_cnt += 1
                rows.append({
                    "entity_id": f"CUST_{1000 + i}",
                    "metric_name": metric_name,
                    "metric_value": round(random.uniform(10.0, 5000.0), 2),
                    "category": category
                })

        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False)
        return output_path, valid_cnt, quar_cnt

    @classmethod
    def generate_rag_documents(cls, count: int = 5) -> List[Dict[str, str]]:
        """
        Generates synthetic RAG text documents with SLAs, technical specs and manuals.
        """
        documents = []
        for i in range(1, count + 1):
            tmpl_title, tmpl_content = random.choice(cls.RAG_TEMPLATES)
            
            doc_id = f"doc_synth_{i}_{str(uuid.uuid4())[:6]}"
            title = tmpl_title.format(
                year=2026,
                code=f"v{i}.0",
                version=f"2.{i}"
            )
            content = tmpl_content.format(
                sla_pct=99.9,
                max_downtime=15,
                soc_id=random.randint(1000, 9999),
                speed_ms=random.randint(12, 45),
                batch_uuid=str(uuid.uuid4())[:8],
                version=f"2.{i}",
                audit_date=datetime.date.today().isoformat()
            )
            documents.append({
                "doc_id": doc_id,
                "title": title,
                "content": content
            })
        return documents
