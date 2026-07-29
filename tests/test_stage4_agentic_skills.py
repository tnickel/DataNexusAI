import pytest
from src.db.models import IngestedRecord, QuarantineRecord
from src.agents.router import AgentRouter
from src.agents.skills import (
    Text2SQLQuerySkill,
    DocumentRAGSkill,
    DataHealthCheckSkill
)


def test_agent_router_registration():
    router = AgentRouter()
    skills = router.list_skills(user_role="admin")
    names = [s["name"] for s in skills]
    assert "text2sql_query" in names
    assert "document_rag_search" in names
    assert "data_health_check" in names


def test_text2sql_skill_execution(db_session):
    rec = IngestedRecord(
        source_file="sales_q1.csv",
        record_batch_id="b1",
        row_number=1,
        entity_id="CUST_100",
        metric_name="revenue",
        metric_value=500.0,
        category="software"
    )
    db_session.add(rec)
    db_session.commit()

    skill = Text2SQLQuerySkill()
    res = skill.execute(params={"category": "software"}, db=db_session, user_role="analyst")

    assert res.status == "SUCCESS"
    assert res.output["record_count"] == 1
    assert res.output["records"][0]["entity_id"] == "CUST_100"


def test_data_health_check_skill(db_session):
    rec = IngestedRecord(
        source_file="file1.csv",
        record_batch_id="b1",
        row_number=1,
        entity_id="CUST_1",
        metric_name="sales",
        metric_value=10.0,
        category="all"
    )
    db_session.add(rec)
    db_session.commit()

    skill = DataHealthCheckSkill()
    res = skill.execute(params={}, db=db_session, user_role="admin")

    assert res.status == "SUCCESS"
    assert res.output["health_status"] == "HEALTHY"
    assert res.output["total_ingested_records"] >= 1
    assert res.output["quarantine_rate_percentage"] == 0.0


def test_agent_router_static_routing(db_session):
    router = AgentRouter()
    
    # Valid route
    res_valid = router.route_and_execute(
        skill_name="data_health_check",
        params={},
        db=db_session,
        user_role="admin"
    )
    assert res_valid.status == "SUCCESS"

    # Invalid route
    res_invalid = router.route_and_execute(
        skill_name="non_existent_skill",
        params={},
        db=db_session,
        user_role="admin"
    )
    assert res_invalid.status == "FAILED"
    assert "Unbekannte Skill-Route" in res_invalid.error


def test_agent_router_rbac_permission_check(db_session):
    router = AgentRouter()
    # data_health_check is restricted to admin and analyst roles only
    res = router.route_and_execute(
        skill_name="data_health_check",
        params={},
        db=db_session,
        user_role="reporting"
    )
    assert res.status == "FORBIDDEN"
    assert "keine Berechtigung" in res.error


def test_fastapi_agent_endpoints(api_client):
    # GET list skills
    res_list = api_client.get(
        "/api/v1/agent/skills",
        headers={"X-API-Key": "key_admin_secret_123"}
    )
    assert res_list.status_code == 200
    skills = res_list.json()["available_skills"]
    assert len(skills) == 3

    # POST execute skill
    res_exec = api_client.post(
        "/api/v1/agent/execute",
        json={
            "skill_name": "data_health_check",
            "params": {}
        },
        headers={"X-API-Key": "key_admin_secret_123"}
    )
    assert res_exec.status_code == 200
    data = res_exec.json()
    assert data["status"] == "SUCCESS"
    assert "health_status" in data["output"]

    # POST execute invalid skill
    res_bad = api_client.post(
        "/api/v1/agent/execute",
        json={
            "skill_name": "invalid_skill_name",
            "params": {}
        },
        headers={"X-API-Key": "key_admin_secret_123"}
    )
    assert res_bad.status_code == 400
