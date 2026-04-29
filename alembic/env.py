import sys
from pathlib import Path
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.common.models.base import BaseModel

# Import all models
from app.modules.appointment.models.base import Appointment
from app.modules.billing.models.base import Invoice, BillingItem, Payment
from app.modules.ehr.models.base import EHR
from app.modules.insurance.models.models import InsuranceDetail, InsuranceClaim
from app.modules.inventory.models.models import InventoryItem, InventoryTransaction
from app.modules.lab.models.models import LabResult
from app.modules.notifications.models.email_template import EmailTemplate
from app.modules.notifications.models.inapp_notification import Notification
from app.modules.notifications.models.notify_log import NotifyLog
from app.modules.patient_portal.models.models import PatientPortalAccess
from app.modules.patients.models.models import Patient
from app.modules.prescription.models.models import Prescription, PrescriptionItem
from app.modules.reports.models.models import ReportLog
from app.modules.room.models.models import Room
from app.modules.schedule.models.schedule import DoctorSchedule
from app.modules.staff.models.doctor_profile import DoctorProfile
from app.modules.staff.models.nurse_profile import NurseProfile
from app.modules.staff.models.receptionist_profile import ReceptionistProfile
from app.modules.staff.models.labtech_profile import LabTechProfile
from app.modules.staff.models.pharmacist_profile import PharmacistProfile
from app.modules.treatment.models.models import Treatment
from app.modules.user.models.base import User

# Alembic Config object
config = context.config

# Convert async database URL to sync URL for migrations
db_url = settings.DATABASE_URL
if db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
elif db_url.startswith("sqlite+aiosqlite://"):
    db_url = db_url.replace("sqlite+aiosqlite://", "sqlite://")
elif db_url.startswith("postgresql://"):
    pass
elif db_url.startswith("sqlite://"):
    pass
else:
    # Default fallback
    pass

config.set_main_option("sqlalchemy.url", db_url)

# Setup logging
if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = BaseModel.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()