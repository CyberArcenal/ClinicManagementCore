from sqlalchemy import event
from sqlalchemy.orm import Session as SQLSession
import inspect
from app.modules.billing.models.base import BillingItem
from app.modules.billing.state_transition_service import BillingItemTransition

def register_billing_item_events():

    @event.listens_for(SQLSession, 'before_flush')
    def capture_billing_item_changes(session, flush_context, instances):
        pending = session.info.setdefault('billing_item_pending', {'new': [], 'updated': [], 'deleted': []})
        for obj in session.new:
            if isinstance(obj, BillingItem):
                pending['new'].append(obj)
        for obj in session.dirty:
            if isinstance(obj, BillingItem):
                state = inspect(obj)
                changes = {}
                for attr in state.attrs:
                    if attr.history.has_changes():
                        changes[attr.key] = attr.value
                if changes:
                    BillingItemTransition(session).on_before_update(obj, changes)
                    pending['updated'].append({'instance': obj, 'changes': changes})
        for obj in session.deleted:
            if isinstance(obj, BillingItem):
                BillingItemTransition(session).on_before_delete(obj)
                pending['deleted'].append(obj)

    @event.listens_for(SQLSession, 'after_commit')
    def process_billing_item_after_commit(session):
        pending = session.info.pop('billing_item_pending', None)
        if not pending:
            return
        ts = BillingItemTransition(session)
        for obj in pending['new']:
            ts.on_after_create(obj)
        for item in pending['updated']:
            ts.on_after_update(item['instance'], item['changes'])
        for obj in pending['deleted']:
            ts.on_after_delete(obj)