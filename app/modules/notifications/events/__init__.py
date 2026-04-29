from .email_template import register_email_template_events
from .inapp_notification import register_notification_events
from .notify_log import register_notify_log_events

def register_events():
    register_email_template_events()
    register_notification_events()
    register_notify_log_events()