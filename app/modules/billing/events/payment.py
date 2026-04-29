from sqlalchemy import event
from sqlalchemy.orm import Session as SQLSession
import inspect
from app.modules.billing.models.base import Payment
from app.modules.billing.state_transition_service import PaymentTransition

def register_payment_events():

    @event.listens_for(SQLSession, 'before_flush')
    def capture_payment_changes(session, flush_context, instances):
        pending = session.info.setdefault('payment_pending', {'new': [], 'updated': [], 'deleted': []})
        for obj in session.new:
            if isinstance(obj, Payment):
                pending['new'].append(obj)
        for obj in session.dirty:
            if isinstance(obj, Payment):
                state = inspect(obj)
                changes = {}
                for attr in state.attrs:
                    if attr.history.has_changes():
                        changes[attr.key] = attr.value
                if changes:
                    PaymentTransition(session).on_before_update(obj, changes)
                    pending['updated'].append({'instance': obj, 'changes': changes})
        for obj in session.deleted:
            if isinstance(obj, Payment):
                PaymentTransition(session).on_before_delete(obj)
                pending['deleted'].append(obj)

    @event.listens_for(SQLSession, 'after_commit')
    def process_payment_after_commit(session):
        pending = session.info.pop('payment_pending', None)
        if not pending:
            return
        ts = PaymentTransition(session)
        for obj in pending['new']:
            ts.on_after_create(obj)
        for item in pending['updated']:
            ts.on_after_update(item['instance'], item['changes'])
        for obj in pending['deleted']:
            ts.on_after_delete(obj)