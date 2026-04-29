import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_claim_unauthorized():
    response = client.post("/api/v1/insurance-claims/", json={})
    assert response.status_code == 401

def test_list_claims_unauthorized():
    response = client.get("/api/v1/insurance-claims/")
    assert response.status_code == 401

@pytest.fixture
def auth_client(auth_client):
    return auth_client

def test_create_claim_missing_fields(auth_client):
    payload = {}
    response = auth_client.post("/api/v1/insurance-claims/", json=payload)
    assert response.status_code == 422

def test_get_claim_not_found(auth_client):
    response = auth_client.get("/api/v1/insurance-claims/99999")
    assert response.status_code == 404

def test_update_claim_not_found(auth_client):
    payload = {"status": "approved"}
    response = auth_client.put("/api/v1/insurance-claims/99999", json=payload)
    assert response.status_code == 404

def test_delete_claim_not_found(auth_client):
    response = auth_client.delete("/api/v1/insurance-claims/99999")
    assert response.status_code == 404

def test_update_claim_status_invalid(auth_client):
    response = auth_client.patch("/api/v1/insurance-claims/99999/status?new_status=bad")
    assert response.status_code == 404  # because claim not found, but could also be 400 for invalid status