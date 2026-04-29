import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app.main import app

client = TestClient(app)

def test_create_invoice_unauthorized():
    response = client.post("/api/v1/invoices/", json={})
    assert response.status_code == 401

def test_list_invoices_unauthorized():
    response = client.get("/api/v1/invoices/")
    assert response.status_code == 401

@pytest.fixture
def auth_client(auth_client):  # from root conftest
    return auth_client

def test_get_invoice_not_found(auth_client):
    response = auth_client.get("/api/v1/invoices/99999")
    assert response.status_code == 404