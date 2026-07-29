from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class ColumnMeta(BaseModel):
    """Metadata for a database column in the semantic layer."""
    column_name: str = Field(..., description="Physical database column name (e.g. col_49_xyz)")
    semantic_name: str = Field(..., description="Human/AI readable semantic name (e.g. total_revenue_eur)")
    data_type: str = Field(..., description="Data type (FLOAT, STRING, INT, DATETIME)")
    description: str = Field(..., description="Detailed description for LLM comprehension")
    is_pii: bool = Field(False, description="Flag indicating if column contains personally identifiable information (PII)")
    allowed_roles: List[str] = Field(default_factory=lambda: ["admin", "analyst", "reporting"], description="Roles allowed to access this column")


class TableMeta(BaseModel):
    """Metadata for a database table in the semantic layer."""
    table_name: str = Field(..., description="Physical table name")
    semantic_name: str = Field(..., description="Human/AI readable table name")
    description: str = Field(..., description="Overview of table contents")
    columns: Dict[str, ColumnMeta] = Field(default_factory=dict)

    def add_column(self, col: ColumnMeta):
        self.columns[col.column_name] = col


class OntologyRegistry:
    """Central registry holding semantic schemas for LLM agent comprehension and RBAC governance."""

    def __init__(self):
        self._tables: Dict[str, TableMeta] = {}
        self._initialize_default_enterprise_ontology()

    def _initialize_default_enterprise_ontology(self):
        """Initializes default enterprise ontology mapping for ingested data."""
        # Ingested Records Table Schema Mapping
        ingested_table = TableMeta(
            table_name="ingested_records",
            semantic_name="EnterpriseMetrics",
            description="Entkoppelte Datenbanktabelle für Geschäftskennzahlen, Kundenmetriken und Transaktionsdaten."
        )
        
        ingested_table.add_column(ColumnMeta(
            column_name="entity_id",
            semantic_name="customer_or_device_identifier",
            data_type="STRING",
            description="Eindeutige Kennung des Kunden, Partners oder Geräts.",
            is_pii=True,
            allowed_roles=["admin", "analyst"]
        ))
        
        ingested_table.add_column(ColumnMeta(
            column_name="metric_name",
            semantic_name="kpi_metric_name",
            data_type="STRING",
            description="Name der gemessenen Geschäftskennzahl (z. B. revenue, transaction_count, churn_score).",
            is_pii=False,
            allowed_roles=["admin", "analyst", "reporting"]
        ))
        
        ingested_table.add_column(ColumnMeta(
            column_name="metric_value",
            semantic_name="kpi_metric_value",
            data_type="FLOAT",
            description="Numerischer Wert der Kennzahl.",
            is_pii=False,
            allowed_roles=["admin", "analyst", "reporting"]
        ))
        
        ingested_table.add_column(ColumnMeta(
            column_name="category",
            semantic_name="business_category",
            data_type="STRING",
            description="Geschäftsbereich oder Produktkategorie (z. B. electronics, software, services).",
            is_pii=False,
            allowed_roles=["admin", "analyst", "reporting"]
        ))

        self._tables[ingested_table.table_name] = ingested_table

    def register_table(self, table_meta: TableMeta):
        self._tables[table_meta.table_name] = table_meta

    def get_table(self, table_name: str) -> Optional[TableMeta]:
        return self._tables.get(table_name)

    def list_tables(self) -> List[TableMeta]:
        return list(self._tables.values())

    def generate_llm_system_prompt(self, user_role: str = "analyst") -> str:
        """Generates a structured system prompt explaining schema to LLM agents based on user RBAC role."""
        prompt_lines = [
            "### ENTERPRISE DATABASE SCHEMA ONTOLOGY ###",
            "Du bist ein präziser Text2SQL-Agent. Verwende die folgenden Tabellen- und Spaltenbeschreibungen für SQL-Abfragen:\n"
        ]

        for table in self._tables.values():
            prompt_lines.append(f"Tabelle: `{table.table_name}` ({table.semantic_name})")
            prompt_lines.append(f"Beschreibung: {table.description}")
            prompt_lines.append("Spalten:")
            
            for col in table.columns.values():
                if user_role in col.allowed_roles:
                    pii_tag = " [PII - Gesichert]" if col.is_pii else ""
                    prompt_lines.append(f"  - `{col.column_name}` ({col.semantic_name}, Typ: {col.data_type}): {col.description}{pii_tag}")
            
            prompt_lines.append("")

        return "\n".join(prompt_lines)
