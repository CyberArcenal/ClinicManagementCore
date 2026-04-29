# scripts/test_appointment_events.py
import datetime
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.modules.appointment.models.base import Appointment

def test():
    db = SessionLocal()
    # Create a dummy appointment
    apt = Appointment(
        patient_id=1,
        doctor_id=1,
        appointment_datetime=datetime.now(),
        status='scheduled'
    )
    db.add(apt)
    db.commit()
    print("Appointment created, check console for state messages.")