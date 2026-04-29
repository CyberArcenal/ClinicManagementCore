import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_pharmacist_unauthorized():
    response = client.post("/api/v1/pharmacists/", json={})
    assert response.status_code == 401

def test_list_pharmacists_unauthorized():
    response = client.get("/api/v1/pharmacists/")
    assert response.status_code == 401

@pytest.fixture
def auth_client(auth_client):
    return auth_client

def test_create_pharmacist_missing_fields(auth_client):
    payload = {}
    response = auth_client.post("/api/v1/pharmacists/", json=payload)
    assert response.status_code == 422

def test_get_pharmacist_not_found(auth_client):
    response = auth_client.get("/api/v1/pharmacists/99999")
    assert response.status_code == 404

def test_update_pharmacist_not_found(auth_client):
    payload = {}
    response = auth_client.put("/api/v1/pharmacists/99999", json=payload)
    assert response.status_code == 404

def test_delete_pharmacist_not_found(auth_client):
    response = auth_client.delete("/api/v1/pharmacists/99999")
    assert response.status_code == 404