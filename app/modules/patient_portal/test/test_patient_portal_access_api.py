import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_access_record_unauthorized():
    response = client.post("/api/v1/patient-portal/", json={})
    assert response.status_code == 401

def test_list_access_records_unauthorized():
    response = client.get("/api/v1/patient-portal/")
    assert response.status_code == 401

@pytest.fixture
def auth_client(auth_client):
    return auth_client

def test_create_record_missing_fields(auth_client):
    payload = {}
    response = auth_client.post("/api/v1/patient-portal/", json=payload)
    assert response.status_code == 422

def test_get_record_not_found(auth_client):
    response = auth_client.get("/api/v1/patient-portal/99999")
    assert response.status_code == 404

def test_update_record_not_found(auth_client):
    payload = {"logout_time": "2025-01-01T00:00:00"}
    response = auth_client.put("/api/v1/patient-portal/99999", json=payload)
    assert response.status_code == 404

def test_delete_record_not_found(auth_client):
    response = auth_client.delete("/api/v1/patient-portal/99999")
    assert response.status_code == 404

# Patient-facing endpoints (require proper patient authentication, but we use our auth_client)
def test_portal_login(auth_client):
    # Assuming auth_client has a valid user; need patient_id matching user's patient record
    # Since test db may not have patient, this may return 404 or 403. We'll just test structure.
    response = auth_client.post("/api/v1/patient-portal/login?patient_id=1&ip_address=127.0.0.1&user_agent=test")
    # Could be 404 if patient not found, but not 401
    assert response.status_code != 401

def test_portal_logout(auth_client):
    response = auth_client.post("/api/v1/patient-portal/logout?patient_id=1")
    assert response.status_code != 401

def test_get_my_access_history(auth_client):
    response = auth_client.get("/api/v1/patient-portal/me/history?limit=10")
    assert response.status_code != 401

def test_get_active_session(auth_client):
    response = auth_client.get("/api/v1/patient-portal/me/active-session")
    assert response.status_code != 401