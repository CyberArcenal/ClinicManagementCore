import asyncio
import datetime
from unittest.mock import patch
import pytest
from sqlalchemy import event
from sqlalchemy.orm import Session
from app.modules.appointment.enums.base import AppointmentStatus
from app.modules.appointment.events.appointment import register_appointment_events
from app.modules.appointment.models.appointment import Appointment
from app.modules.appointment.state_transition_service import AppointmentStateTransition

@pytest.mark.asyncio
async def test_state_transition_on_create(db_session):
    # Register events (they should already be registered, but for safety)
    register_appointment_events()
    # Create an appointment in the session
    apt = Appointment(
        patient_id=1,
        doctor_id=1,
        appointment_datetime=datetime.now(),
        status=AppointmentStatus.SCHEDULED
    )
    db_session.add(apt)
    # We need to capture the after_commit call
    # For testing, we can directly call the hook or use a spy.
    # Here we'll mock the state service method.
    with patch.object(AppointmentStateTransition, 'on_after_create') as mock_after_create:
        await db_session.commit()
        # The event should have triggered on_after_create
        # Because after_commit runs after commit, we need to await?
        # In async tests, the event runs in the same event loop.
        # We'll give it a moment.
        await asyncio.sleep(0.1)
        mock_after_create.assert_called_once()

@pytest.mark.asyncio
async def test_status_change_hook(db_session):
    # Create and commit an appointment
    apt = Appointment(
        patient_id=1,
        doctor_id=1,
        appointment_datetime=datetime.now(),
        status=AppointmentStatus.SCHEDULED
    )
    db_session.add(apt)
    await db_session.commit()
    # Now change status
    apt.status = AppointmentStatus.CONFIRMED
    with patch.object(AppointmentStateTransition, 'on_status_change') as mock_status_change:
        await db_session.commit()
        await asyncio.sleep(0.1)
        mock_status_change.assert_called_once()
        args = mock_status_change.call_args[0]
        assert args[0] == apt
        assert args[1] == AppointmentStatus.SCHEDULED
        assert args[2] == AppointmentStatus.CONFIRMED