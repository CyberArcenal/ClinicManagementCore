from .prescription import register_prescription_events
from .prescription_item import register_prescription_item_events

def register_events():
    register_prescription_events()
    register_prescription_item_events()