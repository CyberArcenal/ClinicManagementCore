# app/models/__init__.py
from app.models.base import Base, BaseModel

# Import all model classes so that Base.metadata knows them
from app.models.user.models import User, DoctorProfile, NurseProfile, ReceptionistProfile, LabTechProfile, PharmacistProfile
from app.models.patient.models import Patient
from app.models.appointment.models import Appointment
from app.models.ehr.models import EHR
from app.models.prescription.models import Prescription, PrescriptionItem
from app.models.lab_result.models import LabResult
from app.models.treatment.models import Treatment
from app.models.billing.models import Invoice, BillingItem, Payment
from app.models.insurance.models import InsuranceDetail, InsuranceClaim
from app.models.staff.models import DoctorSchedule
from app.models.inventory.models import InventoryItem, InventoryTransaction
from app.models.room.models import Room
from app.models.notifications.models import Notification
from app.models.reports.models import ReportLog
from app.models.patient_portal.models import PatientPortalAccess