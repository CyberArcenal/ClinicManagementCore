from typing import Dict, Any
from sqlalchemy.orm import Session
from app.common.state_transition.base import BaseStateTransition
from app.modules.user.models import User
from app.modules.user.models import UserRole

class UserTransition(BaseStateTransition[User]):

    def on_after_create(self, instance: User) -> None:
        print(f"[User] Created: {instance.email} (role: {instance.role})")

    def on_before_update(self, instance: User, changes: Dict[str, Any]) -> None:
        # Prevent changing email after creation
        if "email" in changes:
            raise ValueError("Cannot change email address of existing user")
        # Prevent changing hashed_password directly; use password change method instead
        if "hashed_password" in changes:
            raise ValueError("Use change_password method instead of direct password update")
        # Optional: validate role change permissions (but handled in service)

    def on_after_update(self, instance: User, changes: Dict[str, Any]) -> None:
        if "role" in changes:
            print(f"[User] Role changed to {instance.role} for {instance.email}")
        if "is_active" in changes:
            status = "activated" if instance.is_active else "deactivated"
            print(f"[User] Account {status}: {instance.email}")

    def on_status_change(self, instance: User, old_status: Any, new_status: Any) -> None:
        # This can be used for both is_active and role changes if we want.
        # We'll handle role and is_active separately in the event listener.
        pass

    def on_before_delete(self, instance: User) -> None:
        # Optional: prevent deletion if user has dependencies (e.g., patient record, doctor profile, etc.)
        # Check related profiles
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
        # Also could check appointments they created, etc.
        if instance.created_appointments:
            raise ValueError(f"User has {len(instance.created_appointments)} created appointments")