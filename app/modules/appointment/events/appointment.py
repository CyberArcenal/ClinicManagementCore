from sqlalchemy import event
from sqlalchemy.orm import Session as SQLSession
import inspect
from app.modules.appointment.models.base import Appointment
from app.modules.appointment.state_transition_service import AppointmentStateTransition

def register_appointment_events():
    """Attach SQLAlchemy event listeners for Appointment model."""

    @event.listens_for(SQLSession, 'before_flush')
    def capture_appointment_changes(session, flush_context, instances):
        pending = session.info.setdefault('appointment_pending', {'new': [], 'updated': [], 'deleted': []})
        for obj in session.new:
            if isinstance(obj, Appointment):
                pending['new'].append(obj)
        for obj in session.dirty:
            if isinstance(obj, Appointment):
                state = inspect(obj)
                changes = {}
                old_status = None
                status_changed = False
                for attr in state.attrs:
                    if attr.history.has_changes():
                        new_val = attr.value
                        changes[attr.key] = new_val
                        if attr.key == 'status':
                            status_changed = True
                            old_status = attr.history.deleted[0] if attr.history.deleted else None
                if changes:
                    # Call before_update hook immediately (before flush)
                    state_service = AppointmentStateTransition(session)
                    state_service.on_before_update(obj, changes)
                    pending['updated'].append({
                        'instance': obj,
                        'changes': changes,
                        'old_status': old_status,
                        'status_changed': status_changed
                    })
        for obj in session.deleted:
            if isinstance(obj, Appointment):
                state_service = AppointmentStateTransition(session)
                state_service.on_before_delete(obj)
                pending['deleted'].append(obj)

    @event.listens_for(SQLSession, 'after_commit')
    def process_appointment_after_commit(session):
        pending = session.info.pop('appointment_pending', None)
        if not pending:
            return
        state_service = AppointmentStateTransition(session)
        for obj in pending['new']:
            state_service.on_after_create(obj)
        for item in pending['updated']:
            obj = item['instance']
            changes = item['changes']
            state_service.on_after_update(obj, changes)
            if item['status_changed']:
                state_service.on_status_change(obj, item['old_status'], changes['status'])
        for obj in pending['deleted']:
            state_service.on_after_delete(obj)

    # Optionally, you can also listen to before_commit or after_flush; keep as is.