import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_transaction_unauthorized():
    response = client.post("/api/v1/inventory-transactions/", json={})
    assert response.status_code == 401

def test_list_transactions_unauthorized():
    response = client.get("/api/v1/inventory-transactions/")
    assert response.status_code == 401

@pytest.fixture
def auth_client(auth_client):
    return auth_client

def test_create_transaction_missing_fields(auth_client):
    payload = {}
    response = auth_client.post("/api/v1/inventory-transactions/", json=payload)
    assert response.status_code == 422

def test_get_transaction_not_found(auth_client):
    response = auth_client.get("/api/v1/inventory-transactions/99999")
    assert response.status_code == 404

def test_update_transaction_not_found(auth_client):
    payload = {"reference_document": "PO-X"}
    response = auth_client.put("/api/v1/inventory-transactions/99999", json=payload)
    assert response.status_code == 404

def test_delete_transaction_not_found(auth_client):
    response = auth_client.delete("/api/v1/inventory-transactions/99999")
    assert response.status_code == 404