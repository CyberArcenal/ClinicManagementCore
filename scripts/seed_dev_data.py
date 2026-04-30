#!/usr/bin/env python
"""
Development data seeder for ClinicManagementCore.
Run: python scripts/seed_dev_data.py
"""

import sys
import os
from pathlib import Path
from app.modules.appointment.models.appointment import Appointment
from app.modules.billing.models.billing_item import BillingItem
from app.modules.billing.models.invoice import Invoice
from app.modules.inventory.models.inventory_item import InventoryItem
from app.modules.lab.models.lab import LabResult, LabStatus
from app.modules.notifications.models.email_template import EmailTemplate
from app.modules.patients.models.patient import Patient
from app.modules.prescription.models import Prescription, PrescriptionItem
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta, date
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.modules.user.models import User, UserRole
from app.modules.staff.models.doctor_profile import DoctorProfile
from app.modules.staff.models.nurse_profile import NurseProfile
from app.modules.staff.models.receptionist_profile import ReceptionistProfile
from app.modules.staff.models.labtech_profile import LabTechProfile
from app.modules.staff.models.pharmacist_profile import PharmacistProfile
from app.modules.appointment.enums.base import AppointmentStatus
from app.modules.billing.enums.base import InvoiceStatus, PaymentMethod


# ---------- Helper ----------
def hash_password(plain: str) -> str:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return pwd_context.hash(plain)

# ---------- Connect ----------
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# ---------- Templates (consolidated) ----------
TEMPLATES = [
    # Appointment
    {"name": "appointment_created", "subject": "Appointment Confirmation", "content": "Dear {{ patient_name }},\n\nYour appointment with Dr. {{ doctor_name }} on {{ appointment_datetime }} is confirmed.\n"},
    {"name": "appointment_created_doctor", "subject": "New Appointment Scheduled", "content": "Dear Dr. {{ doctor_name }},\n\nNew appointment with patient {{ patient_name }} on {{ appointment_datetime }}.\n"},
    {"name": "appointment_rescheduled", "subject": "Appointment Rescheduled", "content": "Dear {{ patient_name }},\n\nAppointment moved to {{ new_datetime }}.\n"},
    {"name": "appointment_cancelled", "subject": "Appointment Cancelled", "content": "Dear {{ patient_name }},\n\nAppointment on {{ appointment_datetime }} cancelled.\n"},
    # EHR
    {"name": "ehr_created", "subject": "New Medical Record", "content": "Dear {{ patient_name }},\n\nRecord created on {{ visit_date }}.\n"},
    # Billing
    {"name": "invoice_created", "subject": "New Invoice", "content": "Invoice {{ invoice_number }} amount {{ total }}.\n"},
    {"name": "payment_received", "subject": "Payment Received", "content": "Payment of {{ amount }} received.\n"},
    # Lab
    {"name": "lab_result_ready", "subject": "Lab Results Ready", "content": "Your {{ test_name }} results are ready.\n"},
    # Prescription
    {"name": "prescription_created", "subject": "New Prescription", "content": "Prescription issued by Dr. {{ doctor_name }}.\n"},
    # Staff welcome
    {"name": "staff_welcome_doctor", "subject": "Welcome Doctor", "content": "Welcome Dr. {{ full_name }}!\n"},
    {"name": "staff_welcome_nurse", "subject": "Welcome Nurse", "content": "Welcome Nurse {{ full_name }}!\n"},
    {"name": "staff_welcome_receptionist", "subject": "Welcome Receptionist", "content": "Welcome {{ full_name }}!\n"},
    {"name": "staff_welcome_labtech", "subject": "Welcome Lab Tech", "content": "Welcome {{ full_name }}!\n"},
    {"name": "staff_welcome_pharmacist", "subject": "Welcome Pharmacist", "content": "Welcome {{ full_name }}!\n"},
    # Patient welcome
    {"name": "patient_welcome", "subject": "Welcome", "content": "Dear {{ patient_name }},\n\nThank you for registering.\n"},
    # User welcome
    {"name": "user_welcome", "subject": "Welcome", "content": "Welcome {{ full_name }}!\n"},
    # Portal alert
    {"name": "portal_login_alert", "subject": "Login Alert", "content": "Login from IP {{ ip_address }}.\n"},
    # Inventory
    {"name": "low_stock_alert", "subject": "Low Stock", "content": "Item {{ item_name }} stock low.\n"},
]

def seed_templates(db):
    for t in TEMPLATES:
        existing = db.query(EmailTemplate).filter(EmailTemplate.name == t["name"]).first()
        if not existing:
            db.add(EmailTemplate(**t))
    db.commit()
    print("✅ Email templates seeded")

def seed_users(db):
    # Admin
    admin = db.query(User).filter(User.email == "admin@clinic.com").first()
    if not admin:
        admin = User(
            email="admin@clinic.com",
            hashed_password=hash_password("admin123"),
            full_name="System Admin",
            role=UserRole.ADMIN,
            is_active=True,
            phone_number="+1234567890"
        )
        db.add(admin)
    # Doctor
    doctor_user = db.query(User).filter(User.email == "doctor@clinic.com").first()
    if not doctor_user:
        doctor_user = User(
            email="doctor@clinic.com",
            hashed_password=hash_password("doctor123"),
            full_name="John Smith",
            role=UserRole.DOCTOR,
            is_active=True,
            phone_number="+1234567891"
        )
        db.add(doctor_user)
    # Nurse
    nurse_user = db.query(User).filter(User.email == "nurse@clinic.com").first()
    if not nurse_user:
        nurse_user = User(
            email="nurse@clinic.com",
            hashed_password=hash_password("nurse123"),
            full_name="Jane Doe",
            role=UserRole.NURSE,
            is_active=True,
            phone_number="+1234567892"
        )
        db.add(nurse_user)
    # Receptionist
    rec_user = db.query(User).filter(User.email == "reception@clinic.com").first()
    if not rec_user:
        rec_user = User(
            email="reception@clinic.com",
            hashed_password=hash_password("rec123"),
            full_name="Alice Brown",
            role=UserRole.RECEPTIONIST,
            is_active=True,
            phone_number="+1234567893"
        )
        db.add(rec_user)
    # Lab Tech
    lab_user = db.query(User).filter(User.email == "labtech@clinic.com").first()
    if not lab_user:
        lab_user = User(
            email="labtech@clinic.com",
            hashed_password=hash_password("lab123"),
            full_name="Bob White",
            role=UserRole.LAB_TECH,
            is_active=True,
            phone_number="+1234567894"
        )
        db.add(lab_user)
    # Pharmacist
    pharm_user = db.query(User).filter(User.email == "pharmacist@clinic.com").first()
    if not pharm_user:
        pharm_user = User(
            email="pharmacist@clinic.com",
            hashed_password=hash_password("pharm123"),
            full_name="Eve Green",
            role=UserRole.PHARMACIST,
            is_active=True,
            phone_number="+1234567895"
        )
        db.add(pharm_user)
    # Patient
    patient_user = db.query(User).filter(User.email == "patient@example.com").first()
    if not patient_user:
        patient_user = User(
            email="patient@example.com",
            hashed_password=hash_password("patient123"),
            full_name="Patient One",
            role=UserRole.PATIENT,
            is_active=True,
            phone_number="+1234567896"
        )
        db.add(patient_user)
    db.commit()
    
    # Return created user IDs for profiles
    return {
        "admin": admin,
        "doctor": doctor_user,
        "nurse": nurse_user,
        "receptionist": rec_user,
        "labtech": lab_user,
        "pharmacist": pharm_user,
        "patient": patient_user
    }

def seed_profiles(db, users):
    # Doctor profile
    if not db.query(DoctorProfile).filter(DoctorProfile.user_id == users["doctor"].id).first():
        db.add(DoctorProfile(
            user_id=users["doctor"].id,
            specialization="Cardiology",
            license_number="DOC12345",
            years_of_experience=10
        ))
    # Nurse profile
    if not db.query(NurseProfile).filter(NurseProfile.user_id == users["nurse"].id).first():
        db.add(NurseProfile(
            user_id=users["nurse"].id,
            license_number="NURSE123"
        ))
    # Receptionist profile
    if not db.query(ReceptionistProfile).filter(ReceptionistProfile.user_id == users["receptionist"].id).first():
        db.add(ReceptionistProfile(user_id=users["receptionist"].id))
    # LabTech profile
    if not db.query(LabTechProfile).filter(LabTechProfile.user_id == users["labtech"].id).first():
        db.add(LabTechProfile(user_id=users["labtech"].id))
    # Pharmacist profile
    if not db.query(PharmacistProfile).filter(PharmacistProfile.user_id == users["pharmacist"].id).first():
        db.add(PharmacistProfile(user_id=users["pharmacist"].id))
    db.commit()

def seed_patient_record(db, user):
    if not db.query(Patient).filter(Patient.user_id == user.id).first():
        patient = Patient(
            user_id=user.id,
            date_of_birth=datetime(1990, 1, 1),
            gender="M",
            blood_type="O+",
            address="123 Main St",
            emergency_contact_name="Emergency Contact",
            emergency_contact_phone="+1234567897"
        )
        db.add(patient)
        db.commit()
        return patient
    return db.query(Patient).filter(Patient.user_id == user.id).first()

def seed_appointments(db, patient, doctor):
    # One future appointment
    existing = db.query(Appointment).filter(Appointment.patient_id == patient.id).first()
    if not existing:
        apt = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            appointment_datetime=datetime.now() + timedelta(days=2),
            duration_minutes=30,
            status=AppointmentStatus.SCHEDULED,
            reason="Routine checkup"
        )
        db.add(apt)
        db.commit()

def seed_inventory(db):
    items = [
        {"name": "Paracetamol", "category": "Medicine", "sku": "MED001", "quantity_on_hand": 100, "reorder_level": 20, "unit_cost": 5.0, "selling_price": 10.0},
        {"name": "Bandage", "category": "Supply", "sku": "SUP001", "quantity_on_hand": 200, "reorder_level": 50, "unit_cost": 1.0, "selling_price": 2.0},
    ]
    for data in items:
        existing = db.query(InventoryItem).filter(InventoryItem.sku == data["sku"]).first()
        if not existing:
            db.add(InventoryItem(**data))
    db.commit()

def seed_lab_results(db, patient, doctor):
    existing = db.query(LabResult).first()
    if not existing:
        lab = LabResult(
            patient_id=patient.id,
            requested_by_id=doctor.id,
            test_name="Complete Blood Count",
            requested_date=datetime.now(),
            status=LabStatus.PENDING,
            normal_range="4.5-11.0"
        )
        db.add(lab)
        db.commit()

def seed_prescription(db, patient, doctor):
    existing = db.query(Prescription).first()
    if not existing:
        pres = Prescription(
            patient_id=patient.id,
            doctor_id=doctor.id,
            issue_date=date.today(),
            notes="Take with food"
        )
        db.add(pres)
        db.commit()
        # add item
        item = PrescriptionItem(
            prescription_id=pres.id,
            drug_name="Paracetamol",
            dosage="500mg",
            frequency="3x daily",
            duration_days=5
        )
        db.add(item)
        db.commit()

def seed_billing(db, patient):
    # Create an invoice
    if not db.query(Invoice).first():
        inv = Invoice(
            patient_id=patient.id,
            invoice_number="INV-001",
            issue_date=datetime.now(),
            due_date=datetime.now() + timedelta(days=30),
            subtotal=100.00,
            tax=10.00,
            total=110.00,
            status=InvoiceStatus.DRAFT
        )
        db.add(inv)
        db.commit() 
        # Add item
        item = BillingItem(
            invoice_id=inv.id,
            description="Consultation",
            quantity=1,
            unit_price=100.00,
            total=100.00
        )
        db.add(item)
        db.commit()

def main():
    db = SessionLocal()
    try:
        print("🌱 Seeding development data...")
        seed_templates(db)
        users = seed_users(db)
        seed_profiles(db, users)
        patient = seed_patient_record(db, users["patient"])
        doctor_profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == users["doctor"].id).first()
        if doctor_profile and patient:
            seed_appointments(db, patient, doctor_profile)
        seed_inventory(db)
        if doctor_profile and patient:
            seed_lab_results(db, patient, doctor_profile)
            seed_prescription(db, patient, doctor_profile)
        seed_billing(db, patient)
        print("✅ Seeding completed.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()