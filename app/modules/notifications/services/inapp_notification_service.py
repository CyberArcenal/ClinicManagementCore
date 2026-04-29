# app/modules/notifications/inapp_notification_service.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.sql import func

from app.common.exceptions.user import UserNotFoundError
from app.common.schema.base import PaginatedResponse
from app.modules.notifications.models.inapp_notification import Notification
from app.modules.notifications.schemas.base import NotificationCreate, NotificationUpdate
from app.modules.user.models import User


class InAppNotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    async def get_notification(self, notification_id: int) -> Optional[Notification]:
        result = await self.db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        return result.scalar_one_or_none()

    async def get_user_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        page: int = 1,
        page_size: int = 50,
    ) -> PaginatedResponse[Notification]:
        query = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            query = query.where(Notification.is_read == False)
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)
        # Order and paginate
        query = query.order_by(Notification.created_at.desc())
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        result = await self.db.execute(query)
        items = result.scalars().all()
        pages = (total + page_size - 1) // page_size if total > 0 else 0
        return PaginatedResponse(items=items, total=total, page=page, size=page_size, pages=pages)

    async def create_notification(self, data: NotificationCreate) -> Notification:
        # Validate user and actor exist
        user = await self.db.get(User, data.user_id)
        if not user:
            raise UserNotFoundError(f"User {data.user_id} not found")
        actor = await self.db.get(User, data.actor_id)
        if not actor:
            raise UserNotFoundError(f"Actor {data.actor_id} not found")

        notification = Notification(
            user_id=data.user_id,
            actor_id=data.actor_id,
            notification_type=data.notification_type,
            message=data.message,
            is_read=data.is_read,
            related_id=data.related_id,
            related_model=data.related_model,
        )
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        return notification

    async def update_notification(
        self, notification_id: int, data: NotificationUpdate
    ) -> Optional[Notification]:
        notification = await self.get_notification(notification_id)
        if not notification:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(notification, key, value)
        await self.db.commit()
        await self.db.refresh(notification)
        return notification

    async def delete_notification(self, notification_id: int) -> bool:
        notification = await self.get_notification(notification_id)
        if not notification:
            return False
        await self.db.delete(notification)
        await self.db.commit()
        return True

    # ------------------------------------------------------------------
    # Utilities (status, mark read, count unread)
    # ------------------------------------------------------------------
    async def mark_as_read(self, notification_id: int) -> bool:
        notification = await self.get_notification(notification_id)
        if not notification:
            return False
        notification.is_read = True
        await self.db.commit()
        return True

    async def mark_all_as_read(self, user_id: int) -> int:
        result = await self.db.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)
            .values(is_read=True)
        )
        await self.db.commit()
        return result.rowcount

    async def count_unread(self, user_id: int) -> int:
        result = await self.db.execute(
            select(func.count()).where(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        )
        return result.scalar() or 0

    async def delete_all_for_user(self, user_id: int) -> int:
        result = await self.db.execute(
            select(Notification).where(Notification.user_id == user_id)
        )
        notifs = result.scalars().all()
        for n in notifs:
            await self.db.delete(n)
        await self.db.commit()
        return len(notifs)