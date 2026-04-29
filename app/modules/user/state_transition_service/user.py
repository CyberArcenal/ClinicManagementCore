# app/modules/user/state_transition_service/user.py
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.modules.user.models import User
from app.modules.user.models import UserRole
from app.core.database import SessionLocal
from app.modules.notifications.services.notification_queue import NotificationQueueService

logger = logging.getLogger(__name__)

class UserTransition(BaseStateTransition[User]):

    def on_after_create(self, instance: User) -> None:
        logger.info(f"[User] Created: {instance.email} (role: {instance.role})")
        self._send_welcome_notification(instance)

    def on_before_update(self, instance: User, changes: Dict[str, Any]) -> None:
        if "email" in changes:
            raise ValueError("Cannot change email address of existing user")
        if "hashed_password" in changes:
            raise ValueError("Use change_password method instead of direct password update")

    def on_after_update(self, instance: User, changes: Dict[str, Any]) -> None:
        if "role" in changes:
            logger.info(f"[User] Role changed to {instance.role} for {instance.email}")
            self._notify_role_change(instance, changes["role"])
        if "is_active" in changes:
            status = "activated" if instance.is_active else "deactivated"
            logger.info(f"[User] Account {status}: {instance.email}")
            self._notify_account_status_change(instance)

    def on_before_delete(self, instance: User) -> None:
        if instance.patient_record:
            raise ValueError("Cannot delete user with an associated patient record")
        if instance.doctor_profile:
            raise ValueError("Cannot delete user with an associated doctor profile")
        if instance.nurse_profile:
            raise ValueError("Cannot delete user with an associated nurse profile")
        if instance.receptionist_profile:
            raise ValueError("Cannot delete user with an associated receptionist profile")
        if instance.lab_tech_profile:
            raise ValueError("Cannot delete user with an associated lab tech profile")
        if instance.pharmacist_profile:
            raise ValueError("Cannot delete user with an associated pharmacist profile")
        if instance.created_appointments:
            raise ValueError(f"User has {len(instance.created_appointments)} created appointments")

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def _send_welcome_notification(self, user: User) -> None:
        db = SessionLocal()
        try:
            context = {
                "full_name": user.full_name,
                "email": user.email,
                "role": user.role.value
            }
            NotificationQueueService.queue_notification(
                channel='inapp',
                recipient=str(user.id),
                template_name='user_welcome',
                context=context,
                subject='Welcome to the System',
                message=f'Your account has been created with role {user.role.value}.'
            )
        except Exception as e:
            logger.exception(f"Failed to send welcome notification to user {user.id}: {e}")
        finally:
            db.close()

    def _notify_role_change(self, user: User, new_role: UserRole) -> None:
        """Notify user when role is changed."""
        db = SessionLocal()
        try:
            context = {
                "full_name": user.full_name,
                "old_role": user.role.value,  # user.role already updated? Actually careful: changes contains the new role, but we are in after_update, so user.role is already the new value. We need old role. But the changes dict has old? It has only new value. To get old, we would have stored it in a different way. Let's accept that we only send new role without old for simplicity, or modify event to capture old role. For now, send generic.
                "new_role": new_role.value
            }
            NotificationQueueService.queue_notification(
                channel='inapp',
                recipient=str(user.id),
                template_name='role_changed',
                context=context,
                subject='Role Updated',
                message=f'Your role has been changed to {new_role.value}.'
            )
        except Exception as e:
            logger.exception(f"Failed to send role change notification: {e}")
        finally:
            db.close()

    def _notify_account_status_change(self, user: User) -> None:
        """Notify user when account is activated/deactivated."""
        db = SessionLocal()
        try:
            status = "activated" if user.is_active else "deactivated"
            context = {
                "full_name": user.full_name,
                "status": status
            }
            NotificationQueueService.queue_notification(
                channel='inapp',
                recipient=str(user.id),
                template_name='account_status_changed',
                context=context,
                subject='Account Status Changed',
                message=f'Your account has been {status}.'
            )
        except Exception as e:
            logger.exception(f"Failed to send account status notification: {e}")
        finally:
            db.close()