import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_item_unauthorized():
    response = client.post("/api/v1/prescription-items/", json={})
    assert response.status_code == 401

def test_get_items_by_prescription_unauthorized():
    response = client.get("/api/v1/prescription-items/prescription/1")
    assert response.status_code == 401

@pytest.fixture
def auth_client(auth_client):
    return auth_client

def test_create_item_missing_fields(auth_client):
    payload = {}
    response = auth_client.post("/api/v1/prescription-items/", json=payload)
    assert response.status_code == 422

def test_get_item_not_found(auth_client):
    response = auth_client.get("/api/v1/prescription-items/99999")
    assert response.status_code == 404

def test_update_item_not_found(auth_client):
    payload = {"dosage": "new"}
    response = auth_client.put("/api/v1/prescription-items/99999", json=payload)
    assert response.status_code == 404

def test_delete_item_not_found(auth_client):
    response = auth_client.delete("/api/v1/prescription-items/99999")
    assert response.status_code == 404