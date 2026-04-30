from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.api.db import get_db
from app.common.dependencies.auth import get_current_user, require_role
from app.common.exceptions.user import UserNotFoundError
from app.common.schema.base import PaginatedResponse
from app.common.schema.response import SuccessResponse
from app.common.utils.response import success_response
from app.modules.staff.services.receptionist_profile import ReceptionistProfileService
from app.modules.user.models import User
from app.modules.user.schemas.base import (
    ReceptionistProfileCreate,
    ReceptionistProfileResponse,
    ReceptionistProfileUpdate,
)

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_receptionist_profile(
    data: ReceptionistProfileCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[ReceptionistProfileResponse]:
    service = ReceptionistProfileService(db)
    try:
        receptionist = await service.create_receptionist(data)
        return success_response(data=receptionist, message="Receptionist profile created")
    except UserNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/")
async def list_receptionist_profiles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[PaginatedResponse[ReceptionistProfileResponse]]:
    service = ReceptionistProfileService(db)
    paginated = await service.get_all_receptionists(page=page, page_size=page_size)
    return success_response(data=paginated, message="Receptionist profiles retrieved")


@router.get("/{receptionist_id}")
async def get_receptionist_profile(
    receptionist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[ReceptionistProfileResponse]:
    service = ReceptionistProfileService(db)
    receptionist = await service.get_receptionist(receptionist_id)
    if not receptionist:
        raise HTTPException(status_code=404, detail="Receptionist not found")
    return success_response(data=receptionist, message="Receptionist profile retrieved")


@router.put("/{receptionist_id}")
async def update_receptionist_profile(
    receptionist_id: int,
    data: ReceptionistProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[ReceptionistProfileResponse]:
    service = ReceptionistProfileService(db)
    receptionist = await service.update_receptionist(receptionist_id, data)
    if not receptionist:
        raise HTTPException(status_code=404, detail="Receptionist not found")
    return success_response(data=receptionist, message="Receptionist profile updated")


@router.delete("/{receptionist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_receptionist_profile(
    receptionist_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> None:
    service = ReceptionistProfileService(db)
    deleted = await service.delete_receptionist(receptionist_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Receptionist not found")
    return None