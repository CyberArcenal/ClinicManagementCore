# app/core/state_transition/base.py
from typing import Any, Dict, Optional, TypeVar, Generic
from sqlalchemy.orm import Session

ModelType = TypeVar('ModelType')

class BaseStateTransition(Generic[ModelType]):
    """
    Base class for state transitions of a specific model.
    All hooks are optional; override as needed.
    """
    def __init__(self, db_session: Session):
        self.db = db_session

    # ------------------------------------------------------------------
    # Lifecycle Hooks
    # ------------------------------------------------------------------
    def on_before_create(self, instance: ModelType) -> None:
        """Called before a new instance is inserted (during flush)."""
        pass

    def on_after_create(self, instance: ModelType) -> None:
        """Called after a new instance is inserted."""
        pass

    def on_before_update(self, instance: ModelType, changes: Dict[str, Any]) -> None:
        """
        Called before an instance is updated.
        `changes` is a dict of field name -> new value.
        """
        pass

    def on_after_update(self, instance: ModelType, changes: Dict[str, Any]) -> None:
        """Called after an instance is updated."""
        pass

    def on_before_delete(self, instance: ModelType) -> None:
        """Called before an instance is deleted."""
        pass

    def on_after_delete(self, instance: ModelType) -> None:
        """Called after an instance is deleted."""
        pass

    # ------------------------------------------------------------------
    # Field‑specific hooks (override if needed)
    # ------------------------------------------------------------------
    def on_status_change(self, instance: ModelType, old_status: Any, new_status: Any) -> None:
        """Called when a field named 'status' changes."""
        pass

    @staticmethod
    def extract_changes(instance: ModelType, state) -> Dict[str, Any]:
        """
        Utility to extract changed fields using SQLAlchemy inspector.
        Returns a dict of field_name -> new_value.
        """
        changes = {}
        for attr in state.attrs:
            if attr.history.has_changes():
                changes[attr.key] = attr.value
        return changes