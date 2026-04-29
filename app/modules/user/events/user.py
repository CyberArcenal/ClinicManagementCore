from sqlalchemy import event
from sqlalchemy.orm import Session as SQLSession
import inspect
from app.modules.user.models import User
from app.modules.user.state_transition_service import UserTransition

def register_user_events():

    @event.listens_for(SQLSession, 'before_flush')
    def capture_user_changes(session, flush_context, instances):
        pending = session.info.setdefault('user_pending', {'new': [], 'updated': [], 'deleted': []})
        for obj in session.new:
            if isinstance(obj, User):
                pending['new'].append(obj)
        for obj in session.dirty:
            if isinstance(obj, User):
                state = inspect(obj)
                changes = {}
                role_changed = False
                old_role = None
                active_changed = False
                old_active = None
                for attr in state.attrs:
                    if attr.history.has_changes():
                        new_val = attr.value
                        changes[attr.key] = new_val
                        if attr.key == 'role':
                            role_changed = True
                            old_role = attr.history.deleted[0] if attr.history.deleted else None
                        if attr.key == 'is_active':
                            active_changed = True
                            old_active = attr.history.deleted[0] if attr.history.deleted else None
                if changes:
                    UserTransition(session).on_before_update(obj, changes)
                    pending['updated'].append({
                        'instance': obj,
                        'changes': changes,
                        'role_changed': role_changed,
                        'old_role': old_role,
                        'active_changed': active_changed,
                        'old_active': old_active
                    })
        for obj in session.deleted:
            if isinstance(obj, User):
                UserTransition(session).on_before_delete(obj)
                pending['deleted'].append(obj)

    @event.listens_for(SQLSession, 'after_commit')
    def process_user_after_commit(session):
        pending = session.info.pop('user_pending', None)
        if not pending:
            return
        ts = UserTransition(session)
        for obj in pending['new']:
            ts.on_after_create(obj)
        for item in pending['updated']:
            obj = item['instance']
            changes = item['changes']
            ts.on_after_update(obj, changes)
            # Separate status change for role
            if item['role_changed']:
                ts.on_status_change(obj, item['old_role'], changes['role'])
            if item['active_changed']:
                ts.on_status_change(obj, item['old_active'], changes['is_active'])
        for obj in pending['deleted']:
            ts.on_after_delete(obj)