from sqlalchemy import event
from sqlalchemy.orm import Session as SQLSession
import inspect
from app.modules.staff.models import NurseProfile
from app.modules.staff.state_transition_service import NurseProfileTransition

def register_nurse_events():
    # Same pattern as doctor but for NurseProfile
    @event.listens_for(SQLSession, 'before_flush')
    def capture_nurse_changes(session, flush_context, instances):
        pending = session.info.setdefault('nurse_pending', {'new': [], 'updated': [], 'deleted': []})
        for obj in session.new:
            if isinstance(obj, NurseProfile):
                pending['new'].append(obj)
        for obj in session.dirty:
            if isinstance(obj, NurseProfile):
                state = inspect(obj)
                changes = {}
                for attr in state.attrs:
                    if attr.history.has_changes():
                        changes[attr.key] = attr.value
                if changes:
                    NurseProfileTransition(session).on_before_update(obj, changes)
                    pending['updated'].append({'instance': obj, 'changes': changes})
        for obj in session.deleted:
            if isinstance(obj, NurseProfile):
                NurseProfileTransition(session).on_before_delete(obj)
                pending['deleted'].append(obj)

    @event.listens_for(SQLSession, 'after_commit')
    def process_nurse_after_commit(session):
        pending = session.info.pop('nurse_pending', None)
        if not pending:
            return
        ts = NurseProfileTransition(session)
        for obj in pending['new']:
            ts.on_after_create(obj)
        for item in pending['updated']:
            ts.on_after_update(item['instance'], item['changes'])
        for obj in pending['deleted']:
            ts.on_after_delete(obj)