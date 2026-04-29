from .doctor import register_doctor_events
from .nurse import register_nurse_events
from .receptionist import register_receptionist_events
from .lab_tech import register_lab_tech_events
from .pharmacist import register_pharmacist_events

def register_events():
    register_doctor_events()
    register_nurse_events()
    register_receptionist_events()
    register_lab_tech_events()
    register_pharmacist_events()