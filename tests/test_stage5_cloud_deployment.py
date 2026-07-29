import os
import json
import pytest


def test_nginx_hitnet_config_exists_and_valid():
    conf_path = os.path.join("deploy", "nginx.conf")
    assert os.path.exists(conf_path)
    
    with open(conf_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    assert "datanexus.otc-telekom.de" in content
    assert "allow 10.0.0.0/8;" in content
    assert "deny all;" in content
    assert "Strict-Transport-Security" in content
    assert "ssl_protocols       TLSv1.2 TLSv1.3;" in content


def test_grafana_dashboard_json_valid():
    json_path = os.path.join("deploy", "grafana", "datanexus_monitoring_dashboard.json")
    assert os.path.exists(json_path)
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert data["title"] == "DataNexus AI - Enterprise Operation & Health Dashboard"
    assert len(data["panels"]) >= 4
    
    panel_titles = [p["title"] for p in data["panels"]]
    assert "Ingestion Durchsatz (Records / Sekunde)" in panel_titles
    assert "Quarantäne Quote (%)" in panel_titles
    assert "System Health Status Overview" in panel_titles


def test_deployment_scripts_exist():
    ps1_path = os.path.join("deploy", "deploy_otc.ps1")
    sh_path = os.path.join("deploy", "deploy_otc.sh")
    bat_path = "start.bat"
    app_path = "app.py"
    
    assert os.path.exists(ps1_path)
    assert os.path.exists(sh_path)
    assert os.path.exists(bat_path)
    assert os.path.exists(app_path)
    
    with open(bat_path, "r", encoding="utf-8") as f:
        bat_content = f.read()
    assert "streamlit run app.py" in bat_content
    assert "uvicorn src.api.main:app" in bat_content

    with open(app_path, "r", encoding="utf-8") as f:
        app_content = f.read()
    assert "DataNexus AI – Control Center" in app_content
    assert "Pytest-Suite jetzt ausführen" in app_content


def test_operations_manual_exists():
    manual_path = os.path.join("docs", "BETRIEBSHANDBUCH.md")
    assert os.path.exists(manual_path)
    
    with open(manual_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    assert "Betriebshandbuch" in content
    assert "Key-Person-Dependency" in content
    assert "docker compose up -d" in content
    assert "pg_dump" in content
