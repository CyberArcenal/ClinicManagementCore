from .inventory_item import register_inventory_item_events
from .inventory_transaction import register_inventory_transaction_events

def register_events():
    register_inventory_item_events()
    register_inventory_transaction_events()