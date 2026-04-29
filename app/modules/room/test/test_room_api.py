import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_room_unauthorized():
    response = client.post("/api/v1/rooms/", json={})
    assert response.status_code == 401

def test_list_rooms_unauthorized():
    response = client.get("/api/v1/rooms/")
    assert response.status_code == 401

@pytest.fixture
def auth_client(auth_client):
    return auth_client

def test_create_room_missing_fields(auth_client):
    payload = {}
    response = auth_client.post("/api/v1/rooms/", json=payload)
    assert response.status_code == 422

def test_get_room_not_found(auth_client):
    response = auth_client.get("/api/v1/rooms/99999")
    assert response.status_code == 404

def test_update_room_not_found(auth_client):
    payload = {"room_type": "exam"}
    response = auth_client.put("/api/v1/rooms/99999", json=payload)
    assert response.status_code == 404

def test_delete_room_not_found(auth_client):
    response = auth_client.delete("/api/v1/rooms/99999")
    assert response.status_code == 404

def test_get_available_rooms(auth_client):
    response = auth_client.get("/api/v1/rooms/available")
    assert response.status_code != 401

def test_set_availability_not_found(auth_client):
    response = auth_client.patch("/api/v1/rooms/99999/availability?is_available=false")
    assert response.status_code == 404