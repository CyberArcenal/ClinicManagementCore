from sqlalchemy import event
from sqlalchemy.orm import Session as SQLSession
import inspect
from app.modules.patient_portal.models.models import PatientPortalAccess
from app.modules.patient_portal.state_transition_service import PatientPortalAccessTransition

def register_patient_portal_access_events():

    @event.listens_for(SQLSession, 'before_flush')
    def capture_access_changes(session, flush_context, instances):
        pending = session.info.setdefault('patient_portal_access_pending', {'new': [], 'updated': [], 'deleted': []})
        for obj in session.new:
            if isinstance(obj, PatientPortalAccess):
                pending['new'].append(obj)
        for obj in session.dirty:
            if isinstance(obj, PatientPortalAccess):
                state = inspect(obj)
                changes = {}
                for attr in state.attrs:
                    if attr.history.has_changes():
                        changes[attr.key] = attr.value
                if changes:
                    PatientPortalAccessTransition(session).on_before_update(obj, changes)
                    pending['updated'].append({'instance': obj, 'changes': changes})
        for obj in session.deleted:
            if isinstance(obj, PatientPortalAccess):
                PatientPortalAccessTransition(session).on_before_delete(obj)
                pending['deleted'].append(obj)

    @event.listens_for(SQLSession, 'after_commit')
    def process_access_after_commit(session):
        pending = session.info.pop('patient_portal_access_pending', None)
        if not pending:
            return
        ts = PatientPortalAccessTransition(session)
        for obj in pending['new']:
            ts.on_after_create(obj)
        for item in pending['updated']:
            ts.on_after_update(item['instance'], item['changes'])
        for obj in pending['deleted']:
            ts.on_after_delete(obj)