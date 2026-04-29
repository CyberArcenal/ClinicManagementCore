# app/modules/notifications/enums/base.py
import enum

class TemplateType(str, enum.Enum):
    """Available email/sms/push templates for clinic management."""
    # Appointment
    APPOINTMENT_CREATED = "appointment_created"
    APPOINTMENT_CREATED_DOCTOR = "appointment_created_doctor"
    APPOINTMENT_RESCHEDULED = "appointment_rescheduled"
    APPOINTMENT_RESCHEDULED_DOCTOR = "appointment_rescheduled_doctor"
    APPOINTMENT_CANCELLED = "appointment_cancelled"
    APPOINTMENT_CANCELLED_DOCTOR = "appointment_cancelled_doctor"
    APPOINTMENT_REMINDER = "appointment_reminder"
    APPOINTMENT_REMINDER_DOCTOR = "appointment_reminder_doctor"

    # EHR / Medical Records
    EHR_CREATED = "ehr_created"
    EHR_CREATED_DOCTOR = "ehr_created_doctor"
    EHR_UPDATED = "ehr_updated"
    EHR_UPDATED_DOCTOR = "ehr_updated_doctor"
    EHR_DIAGNOSIS_UPDATED = "ehr_diagnosis_updated"
    EHR_DIAGNOSIS_UPDATED_DOCTOR = "ehr_diagnosis_updated_doctor"
    CRITICAL_DIAGNOSIS_PATIENT = "critical_diagnosis_patient"
    CRITICAL_DIAGNOSIS_DOCTOR = "critical_diagnosis_doctor"
    CRITICAL_DIAGNOSIS_DOCTOR_EMAIL = "critical_diagnosis_doctor_email"

    # Billing & Payments
    INVOICE_CREATED = "invoice_created"
    INVOICE_PAID = "invoice_paid"
    INVOICE_OVERDUE = "invoice_overdue"
    PAYMENT_RECEIVED = "payment_received"
    PAYMENT_RECEIVED_PATIENT = "payment_received"

    # Lab Results
    LAB_REQUEST_CREATED = "lab_request_created"
    LAB_REQUEST_CREATED_DOCTOR = "lab_request_created_doctor"
    LAB_RESULT_READY = "lab_result_ready"
    LAB_RESULT_READY_DOCTOR = "lab_result_ready_doctor"
    LAB_RESULT_CRITICAL = "lab_result_critical"

    # Prescriptions
    PRESCRIPTION_CREATED = "prescription_created"
    PRESCRIPTION_READY = "prescription_ready"
    PRESCRIPTION_DISPENSED = "prescription_dispensed"

    # Patient Portal
    PORTAL_LOGIN_ALERT = "portal_login_alert"
    PORTAL_PASSWORD_CHANGED = "portal_password_changed"
    PORTAL_ACCOUNT_LOCKED = "portal_account_locked"

    # Security & Account
    LOGIN_ALERT = "login_alert"
    TWO_FACTOR_ENABLED = "two_factor_enabled"
    TWO_FACTOR_DISABLED = "two_factor_disabled"
    SECURITY_ALERT = "security_alert"
    PASSWORD_RESET = "password_reset"
    PASSWORD_CHANGED = "password_changed"
    EMAIL_VERIFICATION = "email_verification"

    # General
    WELCOME = "welcome"
    WELCOME_DOCTOR = "welcome_doctor"
    FEEDBACK_REQUEST = "feedback_request"
    SURVEY_INVITATION = "survey_invitation"


class NotificationTypeEnum(str, enum.Enum):
    """In-app notification types (used for Notification model)."""
    # Appointment related
    APPOINTMENT_CREATED = "appointment_created"
    APPOINTMENT_RESCHEDULED = "appointment_rescheduled"
    APPOINTMENT_CANCELLED = "appointment_cancelled"
    APPOINTMENT_REMINDER = "appointment_reminder"
    APPOINTMENT_COMPLETED = "appointment_completed"

    # Medical records
    EHR_CREATED = "ehr_created"
    EHR_UPDATED = "ehr_updated"
    DIAGNOSIS_UPDATED = "diagnosis_updated"
    CRITICAL_DIAGNOSIS = "critical_diagnosis"

    # Billing
    INVOICE_CREATED = "invoice_created"
    INVOICE_PAID = "invoice_paid"
    INVOICE_OVERDUE = "invoice_overdue"
    PAYMENT_RECEIVED = "payment_received"

    # Lab
    LAB_REQUESTED = "lab_requested"
    LAB_RESULT_READY = "lab_result_ready"
    LAB_RESULT_CRITICAL = "lab_result_critical"

    # Prescription
    PRESCRIPTION_CREATED = "prescription_created"
    PRESCRIPTION_READY = "prescription_ready"
    PRESCRIPTION_DISPENSED = "prescription_dispensed"

    # Inventory / Pharmacy
    LOW_STOCK_ALERT = "low_stock_alert"
    MEDICINE_EXPIRY_ALERT = "medicine_expiry_alert"

    # System / Account
    LOGIN_ALERT = "login_alert"
    PASSWORD_CHANGED = "password_changed"
    ACCOUNT_LOCKED = "account_locked"
    WELCOME = "welcome"

    # General
    REMINDER = "reminder"
    INFO = "info"
    ALERT = "alert"


class NotifyStatus(str, enum.Enum):
    """Status of a queued notification log."""
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"
    RESEND = "resend"