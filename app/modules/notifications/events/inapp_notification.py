from sqlalchemy import event
from sqlalchemy.orm import Session as SQLSession
import inspect

from app.modules.notifications.models.inapp_notification import Notification
from app.modules.notifications.state_transition_service.inapp_notification import NotificationTransition

def register_notification_events():

    @event.listens_for(SQLSession, 'before_flush')
    def capture_notification_changes(session, flush_context, instances):
        pending = session.info.setdefault('notification_pending', {'new': [], 'updated': [], 'deleted': []})
        for obj in session.new:
            if isinstance(obj, Notification):
                pending['new'].append(obj)
        for obj in session.dirty:
            if isinstance(obj, Notification):
                state = inspect(obj)
                changes = {}
                is_read_changed = False
                old_is_read = None
                for attr in state.attrs:
                    if attr.history.has_changes():
                        new_val = attr.value
                        changes[attr.key] = new_val
                        if attr.key == 'is_read':
                            is_read_changed = True
                            old_is_read = attr.history.deleted[0] if attr.history.deleted else None
                if changes:
                    NotificationTransition(session).on_before_update(obj, changes)
                    pending['updated'].append({
                        'instance': obj,
                        'changes': changes,
                        'is_read_changed': is_read_changed,
                        'old_is_read': old_is_read
                    })
        for obj in session.deleted:
            if isinstance(obj, Notification):
                NotificationTransition(session).on_before_delete(obj)
                pending['deleted'].append(obj)

    @event.listens_for(SQLSession, 'after_commit')
    def process_notification_after_commit(session):
        pending = session.info.pop('notification_pending', None)
        if not pending:
            return
        ts = NotificationTransition(session)
        for obj in pending['new']:
            ts.on_after_create(obj)
        for item in pending['updated']:
            obj = item['instance']
            changes = item['changes']
            ts.on_after_update(obj, changes)
            if item['is_read_changed'] and 'is_read' in changes:
                ts.on_status_change(obj, item['old_is_read'], changes['is_read'])
        for obj in pending['deleted']:
            ts.on_after_delete(obj)