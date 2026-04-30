# app/modules/insurance/state_transition_service/insurance_claim.py
import logging
from decimal import Decimal
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.core.database import SessionLocal
from app.modules.billing.models.invoice import Invoice
from app.modules.insurance.models.insurance_claim import InsuranceClaim
from app.modules.notifications.services.notification_queue import NotificationQueueService
from app.modules.patients.models.patient import Patient
from app.modules.staff.models.doctor_profile import DoctorProfile

logger = logging.getLogger(__name__)

class InsuranceClaimTransition(BaseStateTransition[InsuranceClaim]):

    def on_after_create(self, instance: InsuranceClaim) -> None:
        logger.info(f"[InsuranceClaim] Created claim {instance.claim_number} for invoice {instance.invoice_id}")

        # Notify patient and doctor
        self._notify_claim_submitted(instance)

    def on_before_update(self, instance: InsuranceClaim, changes: Dict[str, Any]) -> None:
        if "approved_amount" in changes and instance.status == "paid":
            raise ValueError("Cannot change approved amount of a paid claim")

    def on_status_change(self, instance: InsuranceClaim, old_status: str, new_status: str) -> None:
        logger.info(f"[InsuranceClaim] Status changed from {old_status} to {new_status}")

        if new_status == "approved":
            self._update_invoice_with_approved_amount(instance)
            self._notify_claim_approved(instance)
        elif new_status == "paid":
            self._update_invoice_paid(instance)
            self._notify_claim_paid(instance)

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def _update_invoice_with_approved_amount(self, claim: InsuranceClaim) -> None:
        """Update invoice with approved amount (e.g., adjust patient balance)."""
        db = SessionLocal()
        try:
            invoice = db.query(Invoice).filter(Invoice.id == claim.invoice_id).first()
            if invoice and claim.approved_amount is not None:
                # Option 1: Adjust invoice total by deducting approved amount
                # Option 2: Store approved amount as separate field. For simplicity, we just log.
                # Real business logic may involve creating a credit note or adjusting items.
                logger.info(f"Claim {claim.claim_number} approved: {claim.approved_amount} for invoice {invoice.id}")
                # Example: reduce invoice total? Not typical; instead create a separate credit.
        except Exception as e:
            logger.exception(f"Failed to update invoice for claim {claim.id}: {e}")
        finally:
            db.close()

    def _update_invoice_paid(self, claim: InsuranceClaim) -> None:
        """Mark invoice as paid if claim covers full amount."""
        db = SessionLocal()
        try:
            invoice = db.query(Invoice).filter(Invoice.id == claim.invoice_id).first()
            if invoice and claim.approved_amount and claim.approved_amount >= invoice.total:
                invoice.status = 'paid'
                db.commit()
                logger.info(f"Invoice {invoice.id} marked as paid by insurance claim {claim.claim_number}")
        except Exception as e:
            logger.exception(f"Failed to mark invoice as paid: {e}")
        finally:
            db.close()

    def _notify_claim_submitted(self, claim: InsuranceClaim) -> None:
        db = SessionLocal()
        try:
            patient = db.query(Patient).join(Invoice).filter(Invoice.id == claim.invoice_id).first()
            if patient and patient.user_id:
                context = {
                    "patient_name": patient.user.full_name if patient.user else "Patient",
                    "claim_number": claim.claim_number,
                    "invoice_id": claim.invoice_id,
                    "status": claim.status
                }
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(patient.user_id),
                    template_name='claim_submitted',
                    context=context,
                    subject='Insurance Claim Submitted',
                    message=f"Claim {claim.claim_number} has been submitted."
                )
        except Exception as e:
            logger.exception(f"Failed to send claim submitted notification: {e}")
        finally:
            db.close()

    def _notify_claim_approved(self, claim: InsuranceClaim) -> None:
        db = SessionLocal()
        try:
            patient = db.query(Patient).join(Invoice).filter(Invoice.id == claim.invoice_id).first()
            if patient and patient.user_id:
                context = {
                    "patient_name": patient.user.full_name if patient.user else "Patient",
                    "claim_number": claim.claim_number,
                    "approved_amount": str(claim.approved_amount)
                }
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(patient.user_id),
                    template_name='claim_approved',
                    context=context,
                    subject='Insurance Claim Approved',
                    message=f"Your claim {claim.claim_number} has been approved for {claim.approved_amount}."
                )
        except Exception as e:
            logger.exception(f"Failed to send claim approved notification: {e}")
        finally:
            db.close()

    def _notify_claim_paid(self, claim: InsuranceClaim) -> None:
        db = SessionLocal()
        try:
            patient = db.query(Patient).join(Invoice).filter(Invoice.id == claim.invoice_id).first()
            if patient and patient.user_id:
                context = {
                    "patient_name": patient.user.full_name if patient.user else "Patient",
                    "claim_number": claim.claim_number,
                    "amount": str(claim.approved_amount)
                }
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(patient.user_id),
                    template_name='claim_paid',
                    context=context,
                    subject='Insurance Claim Paid',
                    message=f"Claim {claim.claim_number} payment of {claim.approved_amount} received."
                )
        except Exception as e:
            logger.exception(f"Failed to send claim paid notification: {e}")
        finally:
            db.close()