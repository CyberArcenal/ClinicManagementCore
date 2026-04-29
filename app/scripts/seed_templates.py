#!/usr/bin/env python
"""
Seed email templates for the ClinicManagementCore system.
Run: python scripts/seed_templates.py
"""

import sys
import os

from app.modules.notifications.models.email_template import EmailTemplate

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Database URL (can be overridden by env)
DATABASE_URL = settings.DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# ------------------------------------------------------------------
# Template definitions (name, subject, content)
# ------------------------------------------------------------------
TEMPLATES = [
    # Appointment templates
    {
        "name": "appointment_created",
        "subject": "Appointment Confirmation",
        "content": """Dear {{ patient_name }},

Your appointment with Dr. {{ doctor_name }} has been successfully scheduled.

📅 Date & Time: {{ appointment_datetime }}
📍 Location: [Clinic Address]

Please arrive 15 minutes early. If you need to reschedule, please contact us at least 24 hours in advance.

Thank you for choosing us.
""",
    },
    {
        "name": "appointment_created_doctor",
        "subject": "New Appointment Scheduled",
        "content": """Dear Dr. {{ doctor_name }},

A new appointment has been scheduled with patient {{ patient_name }}.

📅 Date & Time: {{ appointment_datetime }}

Please check your calendar for availability.
""",
    },
    {
        "name": "appointment_rescheduled",
        "subject": "Appointment Rescheduled",
        "content": """Dear {{ patient_name }},

Your appointment has been rescheduled.

🕒 Old Date & Time: {{ old_datetime }}
🆕 New Date & Time: {{ new_datetime }}

We apologize for any inconvenience caused.
""",
    },
    {
        "name": "appointment_rescheduled_doctor",
        "subject": "Appointment Rescheduled",
        "content": """Dear Dr. {{ doctor_name }},

The appointment with patient {{ patient_name }} has been rescheduled.

🕒 Old: {{ old_datetime }}
🆕 New: {{ new_datetime }}

Please update your calendar accordingly.
""",
    },
    {
        "name": "appointment_cancelled",
        "subject": "Appointment Cancelled",
        "content": """Dear {{ patient_name }},

Your appointment scheduled on {{ appointment_datetime }} has been cancelled.

If you wish to book another time, please contact us.

We hope to see you soon.
""",
    },
    {
        "name": "appointment_cancelled_doctor",
        "subject": "Appointment Cancelled",
        "content": """Dear Dr. {{ doctor_name }},

The appointment with patient {{ patient_name }} on {{ appointment_datetime }} has been cancelled.

This slot is now free.
""",
    },
    # EHR templates
    {
        "name": "ehr_created",
        "subject": "New Medical Record Created",
        "content": """Dear {{ patient_name }},

A new medical record has been created for you.

📅 Visit Date: {{ visit_date }}
🩺 Diagnosis: {{ diagnosis }}
👨‍⚕️ Doctor: {{ doctor_name }}

You can view full details in your patient portal.
""",
    },
    {
        "name": "ehr_created_doctor",
        "subject": "New EHR Record Created",
        "content": """Dear Dr. {{ doctor_name }},

You have created a new EHR record for patient {{ patient_name }}.

📅 Visit Date: {{ visit_date }}
🩺 Diagnosis: {{ diagnosis }}

Record ID: {{ ehr_id }}
""",
    },
    {
        "name": "ehr_updated",
        "subject": "Medical Record Updated",
        "content": """Dear {{ patient_name }},

Your medical record has been updated.

📅 Last Update: {{ visit_date }}
🩺 Diagnosis: {{ diagnosis }}
👨‍⚕️ Doctor: {{ doctor_name }}

Please log in to your patient portal for full details.
""",
    },
    {
        "name": "ehr_updated_doctor",
        "subject": "EHR Record Updated",
        "content": """Dear Dr. {{ doctor_name }},

You have updated the EHR record for patient {{ patient_name }}.

Patient ID: {{ patient_id }}
EHR ID: {{ ehr_id }}
Updated Diagnosis: {{ diagnosis }}
""",
    },
    {
        "name": "ehr_diagnosis_updated",
        "subject": "Diagnosis Updated",
        "content": """Dear {{ patient_name }},

Your diagnosis has been updated.

🩺 New Diagnosis: {{ diagnosis }}
👨‍⚕️ Doctor: {{ doctor_name }}

Please contact your doctor if you have any questions.
""",
    },
    {
        "name": "ehr_diagnosis_updated_doctor",
        "subject": "Diagnosis Updated for Patient",
        "content": """Dear Dr. {{ doctor_name }},

You have updated the diagnosis for patient {{ patient_name }}.

New Diagnosis: {{ diagnosis }}
""",
    },
    {
        "name": "critical_diagnosis_patient",
        "subject": "⚠️ Critical Diagnosis Alert",
        "content": """Dear {{ patient_name }},

Our records indicate a critical diagnosis: **{{ diagnosis }}**.

Please contact your doctor immediately to discuss next steps.

Doctor: {{ doctor_name }}
Date: {{ visit_date }}

This is an automated alert. Please do not reply to this email.
""",
    },
    {
        "name": "critical_diagnosis_doctor",
        "subject": "CRITICAL: Patient Diagnosis",
        "content": """Dear Dr. {{ doctor_name }},

**URGENT** – Patient {{ patient_name }} has a critical diagnosis: {{ diagnosis }}.

Please review the patient's EHR immediately and take appropriate action.

Patient ID: {{ patient_id }}
Diagnosis Date: {{ visit_date }}

Action required.
""",
    },
    {
        "name": "critical_diagnosis_doctor_email",
        "subject": "URGENT: Critical Diagnosis for Patient",
        "content": """Dear Dr. {{ doctor_name }},

This is an urgent notification.

Patient {{ patient_name }} (ID: {{ patient_id }}) has been diagnosed with:

**{{ diagnosis }}**

Please arrange immediate follow-up.

Thank you.
""",
    },
    # Billing templates
    {
        "name": "invoice_created",
        "subject": "New Invoice Generated",
        "content": """Dear {{ patient_name }},

A new invoice has been generated.

🧾 Invoice Number: {{ invoice_number }}
💰 Total Amount: {{ total }}
📅 Issue Date: {{ issue_date }}

Please make payment before the due date to avoid late fees.
""",
    },
    {
        "name": "invoice_paid",
        "subject": "Invoice Payment Confirmation",
        "content": """Dear {{ patient_name }},

We have received your payment.

🧾 Invoice Number: {{ invoice_number }}
💰 Amount Paid: {{ amount }}
📅 Payment Date: {{ payment_date }}

Thank you for your prompt payment.
""",
    },
    {
        "name": "payment_received",
        "subject": "Payment Received",
        "content": """Dear {{ patient_name }},

A payment of {{ amount }} has been received for invoice {{ invoice_number }}.

Your current balance: {{ balance }}

Thank you.
""",
    },
    # Patient portal templates
    {
        "name": "portal_login_alert",
        "subject": "Patient Portal Login Alert",
        "content": """Dear {{ patient_name }},

We noticed a login to your patient portal from IP address {{ ip_address }} on {{ login_time }}.

If this was not you, please contact us immediately to secure your account.
""",
    },
    # Add these to TEMPLATES list in seed_templates.py
    {
        "name": "insurance_detail_created",
        "subject": "Insurance Policy Added",
        "content": "Dear {{ patient_name }},\n\nYour {{ provider_name }} policy ({{ policy_number }}) has been added to your profile.\nCoverage period: {{ coverage_start }} – {{ coverage_end }}.\n",
    },
    {
        "name": "claim_submitted",
        "subject": "Insurance Claim Submitted",
        "content": "Dear {{ patient_name }},\n\nYour claim {{ claim_number }} for invoice #{{ invoice_id }} has been submitted to insurance.\nStatus: {{ status }}.\n",
    },
    {
        "name": "claim_approved",
        "subject": "Insurance Claim Approved",
        "content": "Dear {{ patient_name }},\n\nYour claim {{ claim_number }} has been approved for {{ approved_amount }}.\n",
    },
    {
        "name": "claim_paid",
        "subject": "Insurance Claim Paid",
        "content": "Dear {{ patient_name }},\n\nYour claim {{ claim_number }} payment of {{ amount }} has been received.\n",
    },
    {
        "name": "low_stock_alert",
        "subject": "⚠️ Low Stock Alert: {{ item_name }}",
        "content": """Dear Pharmacy Team,

The stock level for **{{ item_name }}** (SKU: {{ sku }}) is critically low.

📍 Location: {{ location }}
📦 Current Stock: {{ current_stock }}
⚠️ Reorder Level: {{ reorder_level }}

Category: {{ category }}

Please reorder soon to avoid shortage.

Thank you.
""",
    },
    {
        "name": "lab_request_created",
        "subject": "Lab Test Requested",
        "content": "Dear {{ patient_name }},\n\nA lab test ({{ test_name }}) has been requested by Dr. {{ doctor_name }} on {{ requested_date }}.\nWe will notify you when results are ready.\n",
    },
    {
        "name": "lab_request_created_doctor",
        "subject": "Lab Request Created",
        "content": "Dear Dr. {{ doctor_name }},\n\nLab request for {{ test_name }} has been created for patient {{ patient_name }}.\nRequest ID: {{ lab_id }}\n",
    },
    {
        "name": "lab_result_ready",
        "subject": "Lab Results Ready",
        "content": "Dear {{ patient_name }},\n\nYour lab results for {{ test_name }} are now available.\nPlease log in to the patient portal to view them.\n",
    },
    {
        "name": "lab_result_ready_doctor",
        "subject": "Lab Results Completed",
        "content": "Dear Dr. {{ doctor_name }},\n\nLab results for {{ test_name }} (patient {{ patient_name }}) are complete.\nCompleted on: {{ completed_date }}\nPlease review them.\n",
    },
    {
        "name": "lab_request_cancelled",
        "subject": "Lab Test Cancelled",
        "content": "Dear {{ patient_name }},\n\nThe lab test {{ test_name }} has been cancelled.\n",
    },
    {
        "name": "lab_request_cancelled_doctor",
        "subject": "Lab Request Cancelled",
        "content": "Dear Dr. {{ doctor_name }},\n\nLab request {{ test_name }} for patient {{ patient_name }} has been cancelled.\n",
    },
    {
        "name": "critical_lab_result_doctor",
        "subject": "URGENT: Critical Lab Result",
        "content": "Dear Dr. {{ doctor_name }},\n\n**URGENT** – Patient {{ patient_name }} has a critical lab result for {{ test_name }}.\n\nResult: {{ result_data }}\nNormal Range: {{ normal_range }}\n\nPlease take immediate action.\n",
    },
    {
        "name": "critical_lab_result_doctor_email",
        "subject": "URGENT: Critical Lab Result for Immediate Action",
        "content": "Dear Dr. {{ doctor_name }},\n\nThis is an urgent notification.\n\nPatient {{ patient_name }} (ID: {{ patient_id }}) has a critical lab result for {{ test_name }}.\n\nResult: {{ result_data }}\nNormal Range: {{ normal_range }}\nCompleted: {{ completed_date }}\n\nPlease review and act promptly.\n",
    },
    {
        "name": "portal_login_alert",
        "subject": "Patient Portal Login Alert",
        "content": "Dear {{ patient_name }},\n\nA login to your patient portal was recorded on {{ login_time }} from IP address {{ ip_address }}.\n\nIf this was not you, please contact support immediately.\n",
    },
    {
        "name": "portal_login_alert_email",
        "subject": "Security Alert: Your Patient Portal Was Accessed",
        "content": "Dear {{ patient_name }},\n\nWe detected a login to your patient portal at {{ login_time }} from IP {{ ip_address }} using:\n{{ user_agent }}\n\nIf you did not initiate this login, please secure your account by changing your password.\n\nThank you.\n",
    },
    {
        "name": "patient_welcome",
        "subject": "Welcome to Our Clinic",
        "content": "Dear {{ patient_name }},\n\nYour patient account has been created successfully.\nPatient ID: {{ patient_id }}\n\nYou can now book appointments, view medical records, and receive updates via the patient portal.\n\nThank you for choosing us!\n",
    },
    {
        "name": "patient_welcome_email",
        "subject": "Welcome to [Clinic Name] – Your Patient Account",
        "content": "Dear {{ patient_name }},\n\nWelcome! Your patient account has been set up.\n\nYour registered email: {{ email }}\nPatient ID: {{ patient_id }}\n\nPlease log in to the patient portal to complete your profile.\n\nBest regards,\nClinic Team\n",
    },
    {
        "name": "patient_profile_updated",
        "subject": "Patient Profile Updated",
        "content": "Dear {{ patient_name }},\n\nYour patient profile has been updated. The following fields were changed: {{ changed_fields }}.\n\nIf you did not make these changes, please contact us immediately.\n",
    },
    {
        "name": "prescription_created_patient",
        "subject": "New Prescription Issued",
        "content": "Dear {{ patient_name }},\n\nA new prescription has been created for you by Dr. {{ doctor_name }} on {{ issue_date }}.\nPlease visit the pharmacy to collect your medication.\nPrescription ID: {{ prescription_id }}\n",
    },
    {
        "name": "prescription_created_doctor",
        "subject": "Prescription Created",
        "content": "Dear Dr. {{ doctor_name }},\n\nYou have issued prescription {{ prescription_id }} to patient {{ patient_name }}.\n",
    },
    {
        "name": "prescription_dispensed",
        "subject": "Prescription Ready for Pickup",
        "content": "Dear {{ patient_name }},\n\nYour prescription (ID: {{ prescription_id }}) is now ready for pickup at the pharmacy.\nPlease bring this notification.\n",
    },
    {
        "name": "report_generated",
        "subject": "Your Report is Ready",
        "content": 'Dear {{ user_name }},\n\nThe report "{{ report_name }}" you requested has been generated at {{ generated_at }}.\nParameters: {{ parameters }}\n\nYou can download it from the reports section.\n',
    },
    {
        "name": "room_availability_changed",
        "subject": "Room Availability Update",
        "content": "Dear Staff,\n\nRoom {{ room_number }} ({{ room_type }}) is now {{ status }}.\nCapacity: {{ capacity }}\nNotes: {{ notes }}\n",
    },
    {
        "name": "doctor_schedule_created",
        "subject": "Schedule Created",
        "content": "Dear Dr. {{ doctor_name }},\n\nA new schedule has been created for you on {{ day }} from {{ start_time }} to {{ end_time }}.\n",
    },
    {
        "name": "doctor_schedule_updated",
        "subject": "Schedule Updated",
        "content": "Dear Dr. {{ doctor_name }},\n\nYour schedule for {{ day }} has been updated.\n{% if old_start_time %}Old start: {{ old_start_time }} → New start: {{ start_time }}{% endif %}\n{% if old_end_time %}Old end: {{ old_end_time }} → New end: {{ end_time }}{% endif %}\nAvailable: {{ 'Yes' if is_available else 'No' }}\n",
    },
    {
        "name": "doctor_schedule_deleted",
        "subject": "Schedule Deleted",
        "content": "Dear Dr. {{ doctor_name }},\n\nYour schedule for {{ day }} ({{ start_time }}–{{ end_time }}) has been removed.\n",
    },
    {
        "name": "staff_welcome_doctor",
        "subject": "Welcome to the Medical Team",
        "content": "Dear Dr. {{ full_name }},\n\nYour doctor profile has been created.\nSpecialization: {{ specialization }}\nLicense: {{ license_number }}\n\nYou can now access the doctor portal.\n",
    },
    {
        "name": "staff_welcome_nurse",
        "subject": "Welcome to the Nursing Team",
        "content": "Dear {{ full_name }},\n\nYour nurse profile has been created.\nLicense: {{ license_number }}\n",
    },
    {
        "name": "staff_welcome_receptionist",
        "subject": "Welcome to the Front Desk Team",
        "content": "Dear {{ full_name }},\n\nYour receptionist profile has been created.\n",
    },
    {
        "name": "staff_welcome_labtech",
        "subject": "Welcome to the Laboratory Team",
        "content": "Dear {{ full_name }},\n\nYour lab technician profile has been created.\n",
    },
    {
        "name": "staff_welcome_pharmacist",
        "subject": "Welcome to the Pharmacy Team",
        "content": "Dear {{ full_name }},\n\nYour pharmacist profile has been created.\n",
    },
    {
        "name": "treatment_created_patient",
        "subject": "Treatment Scheduled",
        "content": "Dear {{ patient_name }},\n\nA treatment ({{ procedure_name }}) has been scheduled by Dr. {{ doctor_name }} on {{ performed_date }}.\n\nPlease arrive on time. Notes: {{ notes }}\n",
    },
    {
        "name": "treatment_created_doctor",
        "subject": "Treatment Created",
        "content": "Dear Dr. {{ doctor_name }},\n\nTreatment {{ procedure_name }} for patient {{ patient_name }} has been created.\nDate: {{ performed_date }}\nNotes: {{ notes }}\n",
    },
    {
        "name": "user_welcome",
        "subject": "Welcome to the Clinic System",
        "content": "Dear {{ full_name }},\n\nYour account has been created with role: {{ role }}.\nEmail: {{ email }}\n\nYou can now log in to the system.\n",
    },
    {
        "name": "role_changed",
        "subject": "Your Role Has Been Updated",
        "content": "Dear {{ full_name }},\n\nYour role has been changed to {{ new_role }}.\nIf you have questions, please contact administrator.\n",
    },
    {
        "name": "account_status_changed",
        "subject": "Account Status Updated",
        "content": "Dear {{ full_name }},\n\nYour account has been {{ status }}.\n",
    },
]


def seed_templates():
    db = SessionLocal()
    try:
        inserted = 0
        skipped = 0
        for template_data in TEMPLATES:
            name = template_data["name"]
            existing = (
                db.query(EmailTemplate).filter(EmailTemplate.name == name).first()
            )
            if existing:
                skipped += 1
                continue
            template = EmailTemplate(
                name=name,
                subject=template_data["subject"],
                content=template_data["content"],
            )
            db.add(template)
            inserted += 1
        db.commit()
        print(f"✅ Seeded {inserted} new email templates.")
        print(f"⏭️  Skipped {skipped} existing templates.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding templates: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_templates()
