import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# ------------------------------------------------------------------
# Authentication endpoints (public)
# ------------------------------------------------------------------
def test_register_success():
    payload = {
        "email": "newuser@example.com",
        "full_name": "New User",
        "password": "secure123",
        "role": "patient"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "hashed_password" not in data

def test_register_duplicate_email():
    # First registration already done; attempt duplicate
    payload = {
        "email": "newuser@example.com",
        "full_name": "Another",
        "password": "pass"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400

def test_login_success():
    # Use a known user that exists in test db (created via register or fixture)
    # This test assumes the test database is seeded with a user.
    # For integration, we could register a user then login.
    # Here we'll use credentials from the registration we just did.
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "newuser@example.com", "password": "secure123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid():
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "nonexistent@example.com", "password": "wrong"}
    )
    assert response.status_code == 401

# ------------------------------------------------------------------
# Endpoints requiring authentication
# ------------------------------------------------------------------
@pytest.fixture
def auth_headers():
    # First obtain a token via login
    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "newuser@example.com", "password": "secure123"}
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_get_current_user(auth_headers):
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newuser@example.com"

def test_update_current_user(auth_headers):
    payload = {"full_name": "Updated Name", "phone_number": "1234567890"}
    response = client.put("/api/v1/auth/me", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["phone_number"] == "1234567890"

def test_change_password(auth_headers):
    payload = {"old_password": "secure123", "new_password": "newpass456"}
    response = client.post("/api/v1/auth/me/change-password", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Password changed successfully"
    # Verify we can login with new password
    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "newuser@example.com", "password": "newpass456"}
    )
    assert login_resp.status_code == 200

# ------------------------------------------------------------------
# Admin-only endpoints
# ------------------------------------------------------------------
@pytest.fixture
def admin_headers():
    # Assume a separate admin user exists in test db or use the same user with admin role?
    # For simplicity, you could create an admin during test setup.
    # This test will require an admin token; might be provided by root conftest.
    # We'll reuse the auth_client fixture instead.
    pass

def test_list_users_requires_admin(auth_headers):
    # Regular user should get 403
    response = client.get("/api/v1/auth/", headers=auth_headers)
    assert response.status_code == 403

# Ideally we have an admin_client fixture from conftest that provides admin token.
# Assuming we have an admin client fixture, these tests would look like:
# def test_list_users_with_admin(admin_client):
#     response = admin_client.get("/api/v1/auth/")
#     assert response.status_code == 200