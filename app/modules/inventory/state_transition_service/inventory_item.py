from typing import Dict, Any
from sqlalchemy.orm import Session
from app.core.state_transition.base import BaseStateTransition
from app.modules.inventory.models import InventoryItem

class InventoryItemTransition(BaseStateTransition[InventoryItem]):

    def on_after_create(self, instance: InventoryItem) -> None:
        print(f"[InventoryItem] Created: {instance.name} (SKU: {instance.sku})")

    def on_before_update(self, instance: InventoryItem, changes: Dict[str, Any]) -> None:
        # Prevent changing SKU after creation
        if "sku" in changes:
            raise ValueError("Cannot change SKU of existing inventory item")
        # Prevent negative stock
        if "quantity_on_hand" in changes and changes["quantity_on_hand"] < 0:
            raise ValueError("Quantity on hand cannot be negative")

    def on_after_update(self, instance: InventoryItem, changes: Dict[str, Any]) -> None:
        if "quantity_on_hand" in changes:
            print(f"[InventoryItem] Stock changed for {instance.name}: now {instance.quantity_on_hand}")
            # Optionally trigger low stock alert
            if instance.quantity_on_hand <= instance.reorder_level:
                print(f"[InventoryItem] LOW STOCK: {instance.name} (reorder level {instance.reorder_level})")

    def on_before_delete(self, instance: InventoryItem) -> None:
        # Soft delete: prevent hard delete if there are transactions? We'll allow but warn.
        if instance.transactions:
            print(f"[InventoryItem] Warning: Deleting item with {len(instance.transactions)} transactions")