from sqlalchemy.orm import Session
from app.modules.patients import models
from app.modules.patients.schemas.patient import PatientCreate

def get_patient(db: Session, patient_id: int):
    return db.query(models.Patient).filter(models.Patient.id == patient_id).first()

def get_patient_by_email(db: Session, email: str):
    return db.query(models.Patient).filter(models.Patient.email == email).first()

def get_patients(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Patient).offset(skip).limit(limit).all()

def create_patient(db: Session, patient: PatientCreate):
    fake_hashed_password = patient.email + "notsecure" # Placeholder for now
    db_patient = models.Patient(
        first_name=patient.first_name,
        last_name=patient.last_name,
        email=patient.email,
        phone_number=patient.phone_number,
        date_of_birth=patient.date_of_birth,
    )
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient