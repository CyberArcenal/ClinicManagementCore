# Import the event listeners so they get registered when this module is imported
from .appointment import register_appointment_events

def register_event():
    register_appointment_events()