import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_report_log_unauthorized():
    response = client.post("/api/v1/report-logs/", json={})
    assert response.status_code == 401

def test_list_report_logs_unauthorized():
    response = client.get("/api/v1/report-logs/")
    assert response.status_code == 401

@pytest.fixture
def auth_client(auth_client):
    return auth_client

def test_create_report_log_missing_fields(auth_client):
    payload = {}
    response = auth_client.post("/api/v1/report-logs/", json=payload)
    assert response.status_code == 422

def test_get_report_log_not_found(auth_client):
    response = auth_client.get("/api/v1/report-logs/99999")
    assert response.status_code == 404

def test_update_report_log_not_found(auth_client):
    payload = {"file_path": "new.pdf"}
    response = auth_client.put("/api/v1/report-logs/99999", json=payload)
    assert response.status_code == 404

def test_delete_report_log_not_found(auth_client):
    response = auth_client.delete("/api/v1/report-logs/99999")
    assert response.status_code == 404

def test_get_reports_by_user(auth_client):
    response = auth_client.get("/api/v1/report-logs/user/1?skip=0&limit=10")
    assert response.status_code != 401

def test_get_report_statistics(auth_client):
    response = auth_client.get("/api/v1/report-logs/summary/stats")
    assert response.status_code != 401

def test_cleanup_old_logs(auth_client):
    response = auth_client.delete("/api/v1/report-logs/cleanup/old?days=90")
    assert response.status_code != 401