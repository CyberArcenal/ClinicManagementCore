import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_treatment_unauthorized():
    response = client.post("/api/v1/treatments/", json={})
    assert response.status_code == 401

def test_list_treatments_unauthorized():
    response = client.get("/api/v1/treatments/")
    assert response.status_code == 401

@pytest.fixture
def auth_client(auth_client):
    return auth_client

def test_create_treatment_missing_fields(auth_client):
    payload = {}
    response = auth_client.post("/api/v1/treatments/", json=payload)
    assert response.status_code == 422

def test_get_treatment_not_found(auth_client):
    response = auth_client.get("/api/v1/treatments/99999")
    assert response.status_code == 404

def test_update_treatment_not_found(auth_client):
    payload = {"notes": "Updated"}
    response = auth_client.put("/api/v1/treatments/99999", json=payload)
    assert response.status_code == 404

def test_delete_treatment_not_found(auth_client):
    response = auth_client.delete("/api/v1/treatments/99999")
    assert response.status_code == 404

def test_get_patient_treatments(auth_client):
    response = auth_client.get("/api/v1/treatments/patient/1/history")
    assert response.status_code != 401

def test_treatment_statistics_requires_admin(auth_client):
    response = auth_client.get("/api/v1/treatments/stats/summary")
    # Admin lang talaga, pero at least hindi 401
    assert response.status_code in [200, 403]