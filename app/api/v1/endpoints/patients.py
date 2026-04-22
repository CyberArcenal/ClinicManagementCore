from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import SessionLocal
from app.modules.patients.schemas.patient import PatientCreate, PatientResponse
from app.modules.patients.services import patient_service

router = APIRouter()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/patients/", response_model=PatientResponse)
def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    db_patient = patient_service.get_patient_by_email(db, email=patient.email)
    if db_patient:
        raise HTTPException(status_code=400, detail="Email already registered")
    return patient_service.create_patient(db=db, patient=patient)

@router.get("/patients/", response_model=List[PatientResponse])
def read_patients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    patients = patient_service.get_patients(db, skip=skip, limit=limit)
    return patients