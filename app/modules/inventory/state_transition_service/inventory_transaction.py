# app/modules/inventory/state_transition_service/inventory_transaction.py
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.core.database import SessionLocal
from app.modules.inventory.models.inventory_item import InventoryItem
from app.modules.inventory.models.inventory_transaction import InventoryTransaction
from app.modules.notifications.services.notification_queue import NotificationQueueService

logger = logging.getLogger(__name__)

class InventoryTransactionTransition(BaseStateTransition[InventoryTransaction]):

    def on_after_create(self, instance: InventoryTransaction) -> None:
        logger.info(f"[InventoryTransaction] Stock {instance.transaction_type} of {instance.quantity} for item {instance.item_id}")

        # Optionally, send a notification for significant stock changes (e.g., high quantity purchase)
        self._notify_significant_transaction(instance)

    def on_before_update(self, instance: InventoryTransaction, changes: Dict[str, Any]) -> None:
        if "quantity" in changes or "transaction_type" in changes:
            raise ValueError("Cannot modify quantity or type of existing transaction")
            
    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def _notify_significant_transaction(self, transaction: InventoryTransaction) -> None:
        """Send alert for large purchases or returns (e.g., low stock recovery)."""
        # Only notify for certain transaction types that affect stock significantly
        if transaction.transaction_type not in ['purchase', 'return']:
            return
            
        # Get the item details
        db = SessionLocal()
        try:
            item = db.query(InventoryItem).filter(InventoryItem.id == transaction.item_id).first()
            if not item:
                return
                
            # If the transaction brings stock above a certain threshold, maybe alert inventory manager?
            # For now, just log but could send to manager
            if transaction.transaction_type == 'purchase' and abs(transaction.quantity) > 100:
                # Example: send alert for large purchase (quantity > 100)
                logger.info(f"Large purchase of {abs(transaction.quantity)} units of {item.name}")
                # Could queue notification to manager
        except Exception as e:
            logger.exception(f"Error processing transaction notification: {e}")
        finally:
            db.close()