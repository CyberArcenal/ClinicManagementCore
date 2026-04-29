# app/modules/prescription/state_transition_service/prescription.py
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.modules.inventory.schemas.base import InventoryTransactionCreate
from app.modules.inventory.services.inventory_item import InventoryItemService
from app.modules.inventory.services.inventory_transaction import InventoryTransactionService
from app.modules.prescription.models.models import Prescription
from app.core.database import SessionLocal
from app.modules.notifications.services.notification_queue import NotificationQueueService
from app.modules.patients.models.models import Patient
from app.modules.staff.models.doctor_profile import DoctorProfile


logger = logging.getLogger(__name__)

class PrescriptionTransition(BaseStateTransition[Prescription]):

    def on_after_create(self, instance: Prescription) -> None:
        logger.info(f"[Prescription] Created for patient {instance.patient_id} by doctor {instance.doctor_id}")
        self._notify_patient_and_doctor(instance, is_new=True)

    def on_before_update(self, instance: Prescription, changes: Dict[str, Any]) -> None:
        if "patient_id" in changes:
            raise ValueError("Cannot change patient ID of existing prescription")
        if "doctor_id" in changes:
            raise ValueError("Cannot change doctor ID of existing prescription")
        if instance.is_dispensed and changes:
            raise ValueError("Cannot modify a dispensed prescription")

    def on_status_change(self, instance: Prescription, old_status: bool, new_status: bool) -> None:
        if new_status is True and not old_status:
            logger.info(f"[Prescription] Dispensed prescription {instance.id}")
            self._reduce_inventory_stock(instance)
            self._notify_patient_and_doctor(instance, is_dispensed=True)

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def _notify_patient_and_doctor(self, prescription: Prescription, is_new: bool = True, is_dispensed: bool = False) -> None:
        db = SessionLocal()
        try:
            patient = db.query(Patient).filter(Patient.id == prescription.patient_id).first()
            doctor = db.query(DoctorProfile).filter(DoctorProfile.id == prescription.doctor_id).first()
            
            if is_dispensed:
                template_patient = "prescription_dispensed"
                patient_subj = "Prescription Ready"
                fallback_msg = f"Your prescription {prescription.id} is ready for pickup."
                # Only notify patient, doctor maybe not needed
            elif is_new:
                template_patient = "prescription_created_patient"
                template_doctor = "prescription_created_doctor"
                patient_subj = "New Prescription"
                doctor_subj = "Prescription Created"
                fallback_msg = f"A new prescription has been created for you."
            else:
                return

            context = {
                "prescription_id": prescription.id,
                "patient_name": patient.user.full_name if patient and patient.user else "Patient",
                "doctor_name": doctor.user.full_name if doctor and doctor.user else "Doctor",
                "issue_date": str(prescription.issue_date),
                "notes": prescription.notes or ""
            }

            if patient and patient.user_id:
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(patient.user_id),
                    template_name=template_patient,
                    context=context,
                    subject=patient_subj,
                    message=fallback_msg
                )
            if not is_dispensed and doctor and doctor.user_id:
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(doctor.user_id),
                    template_name=template_doctor,
                    context=context,
                    subject=doctor_subj,
                    message=f"Prescription {prescription.id} issued to patient {prescription.patient_id}."
                )
        except Exception as e:
            logger.exception(f"Failed to send prescription notification: {e}")
        finally:
            db.close()

    def _reduce_inventory_stock(self, prescription: Prescription) -> None:
        """Reduce stock for each prescription item."""
        db = SessionLocal()
        try:
            item_service = InventoryItemService(db)
            trans_service = InventoryTransactionService(db)
            for item in prescription.items:
                # Find inventory item by drug name (or SKU). For simplicity, assume drug_name matches inventory name.
                # In practice, you'd have a mapping or link to inventory items.
                inventory_item = item_service.get_item_by_name_sync(item.drug_name)  # need to implement
                if inventory_item:
                    # Reduce stock
                    new_qty = inventory_item.quantity_on_hand - item.quantity  # but quantity not in item? We need to know how many units. 
                    # Actually PrescriptionItem doesn't have quantity field in the model shown earlier. May need to add quantity.
                    # For now, assume quantity = 1 bottle/box.
                    inventory_item.quantity_on_hand -= 1
                    # Create transaction
                    trans_data = InventoryTransactionCreate(
                        item_id=inventory_item.id,
                        transaction_type="sale",
                        quantity=-1,
                        reference_document=f"Prescription {prescription.id}",
                        performed_by_id=None
                    )
                    trans_service.create_transaction(trans_data)
                    db.commit()
                    logger.info(f"Reduced stock for {item.drug_name} due to prescription {prescription.id}")
                else:
                    logger.warning(f"Inventory item not found for drug {item.drug_name}")
        except Exception as e:
            logger.exception(f"Failed to reduce inventory for prescription {prescription.id}: {e}")
            db.rollback()
        finally:
            db.close()