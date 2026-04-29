

# Register events immediately when this module is imported
from app.modules.appointment.events.appointment import register_appointment_events


register_appointment_events()