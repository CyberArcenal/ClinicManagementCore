from fastapi import APIRouter
from .endpoints.email_template import router as email_template_router
from .endpoints.inapp_notification import router as inapp_notification_router
from .endpoints.notify_log import router as notify_log_router

router = APIRouter()
router.include_router(email_template_router, prefix="/email-templates", tags=["Email Templates"])
router.include_router(inapp_notification_router, prefix="/notifications", tags=["In-App Notifications"])
router.include_router(notify_log_router, prefix="/notify-logs", tags=["Notify Logs"])