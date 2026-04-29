import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_template_unauthorized():
    response = client.post("/api/v1/email-templates/", json={})
    assert response.status_code == 401

def test_list_templates_unauthorized():
    response = client.get("/api/v1/email-templates/")
    assert response.status_code == 401

@pytest.fixture
def auth_client(auth_client):
    return auth_client

def test_create_template_missing_fields(auth_client):
    payload = {}
    response = auth_client.post("/api/v1/email-templates/", json=payload)
    assert response.status_code == 422

def test_get_template_not_found(auth_client):
    response = auth_client.get("/api/v1/email-templates/99999")
    assert response.status_code == 404

def test_update_template_not_found(auth_client):
    payload = {"subject": "Updated"}
    response = auth_client.put("/api/v1/email-templates/99999", json=payload)
    assert response.status_code == 404

def test_delete_template_not_found(auth_client):
    response = auth_client.delete("/api/v1/email-templates/99999")
    assert response.status_code == 404

def test_render_template_not_found(auth_client):
    payload = {"context": {"name": "John"}}
    response = auth_client.post("/api/v1/email-templates/render/nonexistent", json=payload)
    assert response.status_code == 404