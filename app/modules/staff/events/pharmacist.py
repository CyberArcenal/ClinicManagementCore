from sqlalchemy import event
from sqlalchemy.orm import Session as SQLSession
import inspect
from app.modules.staff.models.pharmacist_profile import PharmacistProfile
from app.modules.staff.state_transition_service import PharmacistProfileTransition

def register_pharmacist_events():
    # Similar pattern
    @event.listens_for(SQLSession, 'before_flush')
    def capture_pharmacist_changes(session, flush_context, instances):
        pending = session.info.setdefault('pharmacist_pending', {'new': [], 'updated': [], 'deleted': []})
        for obj in session.new:
            if isinstance(obj, PharmacistProfile):
                pending['new'].append(obj)
        for obj in session.dirty:
            if isinstance(obj, PharmacistProfile):
                state = inspect(obj)
                changes = {}
                for attr in state.attrs:
                    if attr.history.has_changes():
                        changes[attr.key] = attr.value
                if changes:
                    PharmacistProfileTransition(session).on_before_update(obj, changes)
                    pending['updated'].append({'instance': obj, 'changes': changes})
        for obj in session.deleted:
            if isinstance(obj, PharmacistProfile):
                PharmacistProfileTransition(session).on_before_delete(obj)
                pending['deleted'].append(obj)

    @event.listens_for(SQLSession, 'after_commit')
    def process_pharmacist_after_commit(session):
        pending = session.info.pop('pharmacist_pending', None)
        if not pending:
            return
        ts = PharmacistProfileTransition(session)
        for obj in pending['new']:
            ts.on_after_create(obj)
        for item in pending['updated']:
            ts.on_after_update(item['instance'], item['changes'])
        for obj in pending['deleted']:
            ts.on_after_delete(obj)