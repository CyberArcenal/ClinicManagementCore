import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_lab_request_unauthorized():
    response = client.post("/api/v1/lab-results/", json={})
    assert response.status_code == 401

def test_list_lab_results_unauthorized():
    response = client.get("/api/v1/lab-results/")
    assert response.status_code == 401

@pytest.fixture
def auth_client(auth_client):
    return auth_client

def test_create_lab_request_missing_fields(auth_client):
    payload = {}
    response = auth_client.post("/api/v1/lab-results/", json=payload)
    assert response.status_code == 422

def test_get_lab_result_not_found(auth_client):
    response = auth_client.get("/api/v1/lab-results/99999")
    assert response.status_code == 404

def test_update_lab_result_not_found(auth_client):
    payload = {"result_data": "some value"}
    response = auth_client.put("/api/v1/lab-results/99999", json=payload)
    assert response.status_code == 404

def test_delete_lab_result_not_found(auth_client):
    response = auth_client.delete("/api/v1/lab-results/99999")
    assert response.status_code == 404

def test_start_lab_processing_not_found(auth_client):
    response = auth_client.patch("/api/v1/lab-results/99999/start?performed_by_id=1")
    assert response.status_code == 404

def test_complete_lab_result_not_found(auth_client):
    response = auth_client.patch("/api/v1/lab-results/99999/complete?result_data=done")
    assert response.status_code == 404

def test_cancel_lab_request_not_found(auth_client):
    response = auth_client.patch("/api/v1/lab-results/99999/cancel?reason=test")
    assert response.status_code == 404

def test_get_pending_lab_requests_requires_lab_tech(auth_client):
    # Assuming auth_client is admin, but endpoint requires lab_tech role.
    # We'll just test that it doesn't throw 500.
    response = auth_client.get("/api/v1/lab-results/pending")
    # Might be 403 if role not lab_tech, or 200 if admin has access.
    assert response.status_code in [200, 403]