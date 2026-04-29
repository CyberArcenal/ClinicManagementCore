from sqlalchemy import event
from sqlalchemy.orm import Session as SQLSession
import inspect

from app.modules.notifications.models.email_template import EmailTemplate
from app.modules.notifications.state_transition_service.email_template import EmailTemplateTransition

def register_email_template_events():

    @event.listens_for(SQLSession, 'before_flush')
    def capture_email_template_changes(session, flush_context, instances):
        pending = session.info.setdefault('email_template_pending', {'new': [], 'updated': [], 'deleted': []})
        for obj in session.new:
            if isinstance(obj, EmailTemplate):
                pending['new'].append(obj)
        for obj in session.dirty:
            if isinstance(obj, EmailTemplate):
                state = inspect(obj)
                changes = {}
                for attr in state.attrs:
                    if attr.history.has_changes():
                        changes[attr.key] = attr.value
                if changes:
                    EmailTemplateTransition(session).on_before_update(obj, changes)
                    pending['updated'].append({'instance': obj, 'changes': changes})
        for obj in session.deleted:
            if isinstance(obj, EmailTemplate):
                EmailTemplateTransition(session).on_before_delete(obj)
                pending['deleted'].append(obj)

    @event.listens_for(SQLSession, 'after_commit')
    def process_email_template_after_commit(session):
        pending = session.info.pop('email_template_pending', None)
        if not pending:
            return
        ts = EmailTemplateTransition(session)
        for obj in pending['new']:
            ts.on_after_create(obj)
        for item in pending['updated']:
            ts.on_after_update(item['instance'], item['changes'])
        for obj in pending['deleted']:
            ts.on_after_delete(obj)