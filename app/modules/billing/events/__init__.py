from .invoice import register_invoice_events
from .billing_item import register_billing_item_events
from .payment import register_payment_events

def register_events():
    """Called by auto‑discovery to register all billing event listeners."""
    register_invoice_events()
    register_billing_item_events()
    register_payment_events()