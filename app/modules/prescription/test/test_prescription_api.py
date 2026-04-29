import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_prescription_unauthorized():
    response = client.post("/api/v1/prescriptions/", json={})
    assert response.status_code == 401

def test_list_prescriptions_unauthorized():
    response = client.get("/api/v1/prescriptions/")
    assert response.status_code == 401

@pytest.fixture
def auth_client(auth_client):
    return auth_client

def test_create_prescription_missing_fields(auth_client):
    payload = {}
    response = auth_client.post("/api/v1/prescriptions/", json=payload)
    assert response.status_code == 422

def test_get_prescription_not_found(auth_client):
    response = auth_client.get("/api/v1/prescriptions/99999")
    assert response.status_code == 404

def test_update_prescription_not_found(auth_client):
    payload = {"notes": "Updated"}
    response = auth_client.put("/api/v1/prescriptions/99999", json=payload)
    assert response.status_code == 404

def test_dispense_prescription_not_found(auth_client):
    response = auth_client.patch("/api/v1/prescriptions/99999/dispense")
    assert response.status_code == 404

def test_delete_prescription_not_found(auth_client):
    response = auth_client.delete("/api/v1/prescriptions/99999")
    assert response.status_code == 404