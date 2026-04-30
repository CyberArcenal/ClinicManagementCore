from sqlalchemy import event
from sqlalchemy.orm import Session as SQLSession
import inspect
from app.modules.treatment.models.treatment import Treatment
from app.modules.treatment.state_transition_service import TreatmentTransition

def register_treatment_events():

    @event.listens_for(SQLSession, 'before_flush')
    def capture_treatment_changes(session, flush_context, instances):
        pending = session.info.setdefault('treatment_pending', {'new': [], 'updated': [], 'deleted': []})
        for obj in session.new:
            if isinstance(obj, Treatment):
                pending['new'].append(obj)
        for obj in session.dirty:
            if isinstance(obj, Treatment):
                state = inspect(obj)
                changes = {}
                for attr in state.attrs:
                    if attr.history.has_changes():
                        changes[attr.key] = attr.value
                if changes:
                    TreatmentTransition(session).on_before_update(obj, changes)
                    pending['updated'].append({'instance': obj, 'changes': changes})
        for obj in session.deleted:
            if isinstance(obj, Treatment):
                TreatmentTransition(session).on_before_delete(obj)
                pending['deleted'].append(obj)

    @event.listens_for(SQLSession, 'after_commit')
    def process_treatment_after_commit(session):
        pending = session.info.pop('treatment_pending', None)
        if not pending:
            return
        ts = TreatmentTransition(session)
        for obj in pending['new']:
            ts.on_after_create(obj)
        for item in pending['updated']:
            ts.on_after_update(item['instance'], item['changes'])
        for obj in pending['deleted']:
            ts.on_after_delete(obj)