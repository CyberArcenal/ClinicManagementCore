# app/modules/inventory/state_transition_service/inventory_item.py
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.modules.inventory.models.inventory_item import InventoryItem
from app.core.database import SessionLocal
from app.modules.notifications.services.notification_queue import NotificationQueueService
from app.modules.user.models import User  # assuming there's a pharmacy manager role

logger = logging.getLogger(__name__)

class InventoryItemTransition(BaseStateTransition[InventoryItem]):

    def on_after_create(self, instance: InventoryItem) -> None:
        logger.info(f"[InventoryItem] Created: {instance.name} (SKU: {instance.sku})")

    def on_before_update(self, instance: InventoryItem, changes: Dict[str, Any]) -> None:
        if "sku" in changes:
            raise ValueError("Cannot change SKU of existing inventory item")
        if "quantity_on_hand" in changes and changes["quantity_on_hand"] < 0:
            raise ValueError("Quantity on hand cannot be negative")

    def on_after_update(self, instance: InventoryItem, changes: Dict[str, Any]) -> None:
        if "quantity_on_hand" in changes:
            old_qty = None  # We don't have old value here easily, but we can log new value
            logger.info(f"[InventoryItem] Stock changed for {instance.name}: now {instance.quantity_on_hand}")
            
            # Trigger low stock alert if below reorder level
            if instance.quantity_on_hand <= instance.reorder_level:
                self._send_low_stock_alert(instance)
                
        if "expiry_date" in changes:
            logger.info(f"[InventoryItem] Expiry date updated for {instance.name}: {instance.expiry_date}")
            
    def on_before_delete(self, instance: InventoryItem) -> None:
        if instance.transactions:
            logger.warning(f"Deleting item {instance.id} with {len(instance.transactions)} transactions")
            
    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def _send_low_stock_alert(self, item: InventoryItem) -> None:
        """Send notification to pharmacy manager (or relevant users) about low stock."""
        # You can fetch users with role = 'pharmacist' or 'admin' and notify them.
        # For simplicity, we'll assume a configurable list of user IDs.
        # Example: fetch all users with role 'pharmacist'
        db = SessionLocal()
        try:
            # Get pharmacy managers (role = pharmacist or admin)
            # In a real system, you'd have a setting or a flag.
            recipients = db.query(User).filter(User.role.in_(['pharmacist', 'admin'])).all()
            context = {
                "item_name": item.name,
                "current_stock": item.quantity_on_hand,
                "reorder_level": item.reorder_level,
                "sku": item.sku,
                "location": item.location or "Main Pharmacy",
                "category": item.category or "General"
            }
            for recipient in recipients:
                NotificationQueueService.queue_notification(
                    channel='inapp',
                    recipient=str(recipient.id),
                    template_name='low_stock_alert',
                    context=context,
                    subject='⚠️ Low Stock Alert',
                    message=f"{item.name} stock is below reorder level ({item.quantity_on_hand} left)."
                )
            logger.info(f"Low stock alert sent for item {item.id}")
        except Exception as e:
            logger.exception(f"Failed to send low stock alert for {item.id}: {e}")
        finally:
            db.close()