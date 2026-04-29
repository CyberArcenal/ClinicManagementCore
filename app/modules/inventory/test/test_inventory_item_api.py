import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_item_unauthorized():
    response = client.post("/api/v1/inventory-items/", json={})
    assert response.status_code == 401

def test_list_items_unauthorized():
    response = client.get("/api/v1/inventory-items/")
    assert response.status_code == 401

@pytest.fixture
def auth_client(auth_client):
    return auth_client

def test_create_item_missing_fields(auth_client):
    payload = {}
    response = auth_client.post("/api/v1/inventory-items/", json=payload)
    assert response.status_code == 422

def test_get_item_not_found(auth_client):
    response = auth_client.get("/api/v1/inventory-items/99999")
    assert response.status_code == 404

def test_update_item_not_found(auth_client):
    payload = {"name": "Updated"}
    response = auth_client.put("/api/v1/inventory-items/99999", json=payload)
    assert response.status_code == 404

def test_delete_item_not_found(auth_client):
    response = auth_client.delete("/api/v1/inventory-items/99999")
    assert response.status_code == 404

def test_add_stock_bad_quantity(auth_client):
    response = auth_client.patch("/api/v1/inventory-items/1/add-stock?quantity=-5")
    assert response.status_code == 400  # validation error