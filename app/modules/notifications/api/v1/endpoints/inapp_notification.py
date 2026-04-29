# app/modules/notification/api/v1/endpoints/inapp_notification.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.user.models import User

router = APIRouter()


@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(
    data: NotificationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create an in-app notification. Usually called by system or other actions.
    """
    service = InAppNotificationService(db)
    try:
        notification = await service.create_notification(data)
        return notification
    except UserNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/me", response_model=List[NotificationResponse])
async def get_my_notifications(
    unread_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InAppNotificationService(db)
    notifications = await service.get_user_notifications(
        user_id=current_user.id,
        unread_only=unread_only,
        skip=skip,
        limit=limit,
    )
    return notifications


@router.get("/me/unread-count", response_model=dict)
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InAppNotificationService(db)
    count = await service.count_unread(current_user.id)
    return {"unread_count": count}


@router.patch("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InAppNotificationService(db)
    success = await service.mark_as_read(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Marked as read"}


@router.patch("/me/read-all")
async def mark_all_as_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InAppNotificationService(db)
    count = await service.mark_all_as_read(current_user.id)
    return {"marked_count": count}


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InAppNotificationService(db)
    deleted = await service.delete_notification(notification_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Notification not found")
    return None