import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_patient_unauthorized():
    response = client.post("/api/v1/patients/", json={})
    assert response.status_code == 401

def test_list_patients_unauthorized():
    response = client.get("/api/v1/patients/")
    assert response.status_code == 401

@pytest.fixture
def auth_client(auth_client):
    return auth_client

def test_create_patient_missing_fields(auth_client):
    payload = {}
    response = auth_client.post("/api/v1/patients/", json=payload)
    assert response.status_code == 422

def test_get_patient_not_found(auth_client):
    response = auth_client.get("/api/v1/patients/99999")
    assert response.status_code == 404

def test_update_patient_not_found(auth_client):
    payload = {"gender": "F"}
    response = auth_client.put("/api/v1/patients/99999", json=payload)
    assert response.status_code == 404

def test_delete_patient_not_found(auth_client):
    response = auth_client.delete("/api/v1/patients/99999")
    assert response.status_code == 404

def test_search_patients(auth_client):
    response = auth_client.get("/api/v1/patients/search/john?skip=0&limit=10")
    # May be 200 even with empty list, not 401
    assert response.status_code != 401

def test_get_patient_summary_not_found(auth_client):
    response = auth_client.get("/api/v1/patients/99999/summary")
    assert response.status_code == 404

def test_get_birthdays_today(auth_client):
    response = auth_client.get("/api/v1/patients/birthdays/today")
    assert response.status_code != 401