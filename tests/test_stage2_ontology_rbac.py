import pytest
from src.db.models import IngestedRecord
from src.ontology.schema_registry import OntologyRegistry


@pytest.fixture(autouse=True)
def seed_test_data(db_session):
    """Populates sample records before each test."""
    rec1 = IngestedRecord(
        source_file="test_sales.csv",
        record_batch_id="batch_001",
        row_number=1,
        entity_id="CUST_SECRET_999",
        metric_name="revenue",
        metric_value=2500.0,
        category="electronics",
        raw_data={"entity_id": "CUST_SECRET_999", "metric_value": 2500.0}
    )
    db_session.add(rec1)
    db_session.commit()


def test_ontology_prompt_generation():
    registry = OntologyRegistry()
    prompt = registry.generate_llm_system_prompt(user_role="analyst")
    
    assert "### ENTERPRISE DATABASE SCHEMA ONTOLOGY ###" in prompt
    assert "ingested_records" in prompt
    assert "customer_or_device_identifier" in prompt


def test_health_check_endpoint(api_client):
    response = api_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "HEALTHY"


def test_ontology_schemas_endpoint(api_client):
    response = api_client.get(
        "/api/v1/ontology/schemas",
        headers={"X-API-Key": "key_analyst_secret_456"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["agent_role"] == "analyst"
    assert "ingested_records" in data["system_prompt"]


def test_rbac_admin_full_access(api_client):
    """Admin Agent should see unrestricted entity_id."""
    response = api_client.get(
        "/api/v1/data/records",
        headers={"X-API-Key": "key_admin_secret_123"}
    )
    assert response.status_code == 200
    records = response.json()["records"]
    assert len(records) >= 1
    assert records[0]["entity_id"] == "CUST_SECRET_999"


def test_rbac_reporting_agent_restricted_access(api_client):
    """Reporting Agent should have entity_id masked with [RESTRICTED_BY_RBAC]."""
    response = api_client.get(
        "/api/v1/data/records",
        headers={"X-API-Key": "key_reporting_secret_789"}
    )
    assert response.status_code == 200
    records = response.json()["records"]
    assert len(records) >= 1
    assert records[0]["entity_id"] == "[RESTRICTED_BY_RBAC]"
    assert records[0]["metric_value"] == 2500.0
