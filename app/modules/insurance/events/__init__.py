from .insurance_detail import register_insurance_detail_events
from .insurance_claim import register_insurance_claim_events

def register_events():
    register_insurance_detail_events()
    register_insurance_claim_events()