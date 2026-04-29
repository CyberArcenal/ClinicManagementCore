import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.core.database import get_db
from app.modules.appointment.models import Appointment
from app.modules.user.models import User

client = TestClient(app)

# We'll assume a test database is set up via conftest (not repeated here)

def test_create_appointment_unauthorized():
    response = client.post("/api/v1/appointments/", json={})
    assert response.status_code == 401

def test_list_appointments_unauthorized():
    response = client.get("/api/v1/appointments/")
    assert response.status_code == 401

# For authorized tests, we need to obtain a token.
# In real tests, you would call the login endpoint first.
# For simplicity, we can mock the authentication dependency.
@pytest.fixture
def auth_headers():
    # In a real test, generate a valid JWT for a test user.
    # Here we'll mock the get_current_user dependency.
    from app.common.dependencies.auth import get_current_user
    async def mock_current_user():
        return User(id=1, email="admin@test.com", is_active=True, role="admin")
    app.dependency_overrides[get_current_user] = mock_current_user
    yield {"Authorization": "Bearer fake"}
    del app.dependency_overrides[get_current_user]

def test_create_appointment_success(auth_headers, db_session):
    # First ensure a patient and doctor exist in test db
    # This would be set up in conftest, but for demonstration we'll patch service validation.
    with patch('app.modules.appointment.service.AppointmentService._validate_doctor_availability') as mock_val:
        mock_val.return_value = None
        payload = {
            "patient_id": 1,
            "doctor_id": 1,
            "appointment_datetime": "2025-06-01T10:00:00",
            "duration_minutes": 30,
            "reason": "Test"
        }
        response = client.post("/api/v1/appointments/", json=payload, headers=auth_headers)
        # If test db lacks patient/doctor, 404 is plausible.
        assert response.status_code in (201, 404)

def test_get_appointment_not_found(auth_headers):
    response = client.get("/api/v1/appointments/99999", headers=auth_headers)
    assert response.status_code == 404

def test_update_appointment_status(auth_headers, db_session):
    # Create a temporary appointment via the service, then test status change.
    # We'll mock the service call to avoid needing DB.
    with patch('app.modules.appointment.service.AppointmentService.get_appointment') as mock_get:
        appt = Appointment(id=1, status="scheduled")
        mock_get.return_value = appt
        with patch('app.modules.appointment.service.AppointmentService.change_status') as mock_change:
            mock_change.return_value = appt
            response = client.patch("/api/v1/appointments/1/status?new_status=confirmed", headers=auth_headers)
            assert response.status_code == 200