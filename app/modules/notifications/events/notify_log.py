import asyncio
from sqlalchemy import event
from sqlalchemy.orm import Session as SQLSession
import inspect

from app.modules.notifications.models.notify_log import NotifyLog
from app.modules.notifications.state_transition_service.notify_log import NotifyLogTransition

def register_notify_log_events():

    @event.listens_for(SQLSession, 'before_flush')
    def capture_notify_log_changes(session, flush_context, instances):
        pending = session.info.setdefault('notify_log_pending', {'new': [], 'updated': [], 'deleted': []})
        for obj in session.new:
            if isinstance(obj, NotifyLog):
                pending['new'].append(obj)
        for obj in session.dirty:
            if isinstance(obj, NotifyLog):
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
                    NotifyLogTransition(session).on_before_update(obj, changes)
                    pending['updated'].append({
                        'instance': obj,
                        'changes': changes,
                        'status_changed': status_changed,
                        'old_status': old_status
                    })
        for obj in session.deleted:
            if isinstance(obj, NotifyLog):
                NotifyLogTransition(session).on_before_delete(obj)
                pending['deleted'].append(obj)

    @event.listens_for(SQLSession, 'after_commit')
    def process_notify_log_after_commit(session):
        pending = session.info.pop('notify_log_pending', None)
        if not pending:
            return
        ts = NotifyLogTransition(session)
        for obj in pending['new']:
            asyncio.create_task(ts.on_after_create(obj))
        for item in pending['updated']:
            obj = item['instance']
            changes = item['changes']
            ts.on_after_update(obj, changes)
            if item['status_changed']:
                ts.on_status_change(obj, item['old_status'], changes['status'])
        for obj in pending['deleted']:
            ts.on_after_delete(obj)