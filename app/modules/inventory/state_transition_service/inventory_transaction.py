from typing import Dict, Any
from sqlalchemy.orm import Session
from app.core.state_transition.base import BaseStateTransition
from app.modules.inventory.models import InventoryTransaction

class InventoryTransactionTransition(BaseStateTransition[InventoryTransaction]):

    def on_after_create(self, instance: InventoryTransaction) -> None:
        print(f"[InventoryTransaction] Stock {instance.transaction_type} of {instance.quantity} for item {instance.item_id}")

    def on_before_update(self, instance: InventoryTransaction, changes: Dict[str, Any]) -> None:
        # Prevent changing quantity or type after creation
        if "quantity" in changes or "transaction_type" in changes:
            raise ValueError("Cannot modify quantity or type of existing transaction")