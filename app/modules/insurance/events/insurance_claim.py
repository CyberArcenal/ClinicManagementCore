from sqlalchemy import event
from sqlalchemy.orm import Session as SQLSession
import inspect
from app.modules.insurance.models.models import InsuranceClaim
from app.modules.insurance.state_transition_service import InsuranceClaimTransition

def register_insurance_claim_events():

    @event.listens_for(SQLSession, 'before_flush')
    def capture_insurance_claim_changes(session, flush_context, instances):
        pending = session.info.setdefault('insurance_claim_pending', {'new': [], 'updated': [], 'deleted': []})
        for obj in session.new:
            if isinstance(obj, InsuranceClaim):
                pending['new'].append(obj)
        for obj in session.dirty:
            if isinstance(obj, InsuranceClaim):
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
                    InsuranceClaimTransition(session).on_before_update(obj, changes)
                    pending['updated'].append({
                        'instance': obj,
                        'changes': changes,
                        'old_status': old_status,
                        'status_changed': status_changed
                    })
        for obj in session.deleted:
            if isinstance(obj, InsuranceClaim):
                InsuranceClaimTransition(session).on_before_delete(obj)
                pending['deleted'].append(obj)

    @event.listens_for(SQLSession, 'after_commit')
    def process_insurance_claim_after_commit(session):
        pending = session.info.pop('insurance_claim_pending', None)
        if not pending:
            return
        ts = InsuranceClaimTransition(session)
        for obj in pending['new']:
            ts.on_after_create(obj)
        for item in pending['updated']:
            obj = item['instance']
            changes = item['changes']
            ts.on_after_update(obj, changes)
            if item['status_changed']:
                ts.on_status_change(obj, item['old_status'], changes['status'])
        for obj in pending['deleted']:
            ts.on_after_delete(obj)