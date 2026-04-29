from sqlalchemy import event
from sqlalchemy.orm import Session as SQLSession
import inspect
from app.modules.prescription.models import Prescription
from app.modules.prescription.state_transition_service import PrescriptionTransition

def register_prescription_events():

    @event.listens_for(SQLSession, 'before_flush')
    def capture_prescription_changes(session, flush_context, instances):
        pending = session.info.setdefault('prescription_pending', {'new': [], 'updated': [], 'deleted': []})
        for obj in session.new:
            if isinstance(obj, Prescription):
                pending['new'].append(obj)
        for obj in session.dirty:
            if isinstance(obj, Prescription):
                state = inspect(obj)
                changes = {}
                old_dispensed = None
                dispensed_changed = False
                for attr in state.attrs:
                    if attr.history.has_changes():
                        new_val = attr.value
                        changes[attr.key] = new_val
                        if attr.key == 'is_dispensed':
                            dispensed_changed = True
                            old_dispensed = attr.history.deleted[0] if attr.history.deleted else None
                if changes:
                    PrescriptionTransition(session).on_before_update(obj, changes)
                    pending['updated'].append({
                        'instance': obj,
                        'changes': changes,
                        'dispensed_changed': dispensed_changed,
                        'old_dispensed': old_dispensed
                    })
        for obj in session.deleted:
            if isinstance(obj, Prescription):
                PrescriptionTransition(session).on_before_delete(obj)
                pending['deleted'].append(obj)

    @event.listens_for(SQLSession, 'after_commit')
    def process_prescription_after_commit(session):
        pending = session.info.pop('prescription_pending', None)
        if not pending:
            return
        ts = PrescriptionTransition(session)
        for obj in pending['new']:
            ts.on_after_create(obj)
        for item in pending['updated']:
            obj = item['instance']
            changes = item['changes']
            ts.on_after_update(obj, changes)
            if item['dispensed_changed']:
                ts.on_status_change(obj, item['old_dispensed'], changes['is_dispensed'])
        for obj in pending['deleted']:
            ts.on_after_delete(obj)