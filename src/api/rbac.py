from typing import List, Dict, Any
from src.ontology.schema_registry import OntologyRegistry
from src.api.auth import AgentUser


class RBACFilterEngine:
    """Enforces role-based column-level access control and PII masking for AI agent data queries."""

    def __init__(self, ontology: OntologyRegistry):
        self.ontology = ontology

    def filter_record_dict(self, table_name: str, record_dict: Dict[str, Any], agent: AgentUser) -> Dict[str, Any]:
        """Filters a single record dictionary based on agent's role and table schema."""
        table_meta = self.ontology.get_table(table_name)
        if not table_meta:
            return record_dict

        filtered = {}
        for col_name, val in record_dict.items():
            if col_name in table_meta.columns:
                col_meta = table_meta.columns[col_name]
                if agent.role in col_meta.allowed_roles:
                    filtered[col_name] = val
                else:
                    # Mask PII / Restricted field for unauthorized roles
                    filtered[col_name] = "[RESTRICTED_BY_RBAC]"
            else:
                filtered[col_name] = val

        return filtered

    def filter_records_list(self, table_name: str, records: List[Dict[str, Any]], agent: AgentUser) -> List[Dict[str, Any]]:
        """Filters a list of record dictionaries based on agent's role."""
        return [self.filter_record_dict(table_name, rec, agent) for rec in records]
