from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.api.db import get_db
from app.common.dependencies.auth import get_current_user, require_role
from app.common.schema.base import PaginatedResponse
from app.common.schema.response import SuccessResponse
from app.common.utils.response import success_response
from app.modules.user.services.user import UserService
from app.modules.user.schemas.base import Token, UserCreate, UserResponse, UserUpdate
from app.modules.user.models import User
from app.core.config import settings
from app.common.exceptions.user import (
    UserNotFoundError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
)

router = APIRouter()


# ------------------------------------------------------------------
# Authentication endpoints (no wrapper – keep token format)
# ------------------------------------------------------------------
@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    service = UserService(db)
    user = await service.authenticate(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = service.create_access_token(
        data={"sub": str(user.id), "role": user.role.value},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse[UserResponse]:
    service = UserService(db)
    try:
        user = await service.create_user(data)
        return success_response(data=user, message="User registered successfully")
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Token:
    service = UserService(db)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = service.create_access_token(
        data={"sub": str(current_user.id), "role": current_user.role.value},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


# ------------------------------------------------------------------
# User CRUD endpoints (wrapped)
# ------------------------------------------------------------------
@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[UserResponse]:
    return success_response(data=current_user, message="Current user retrieved")


@router.put("/me")
async def update_current_user(
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[UserResponse]:
    service = UserService(db)
    try:
        updated = await service.update_user(current_user.id, data)
        return success_response(data=updated, message="User updated")
    except (UserNotFoundError, UserAlreadyExistsError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/me/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[None]:
    service = UserService(db)
    success = await service.change_password(current_user.id, old_password, new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Incorrect old password")
    return success_response(data=None, message="Password changed successfully")


@router.get("/")
async def list_users(
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    email_contains: Optional[str] = Query(None),
    full_name_contains: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[PaginatedResponse[UserResponse]]:
    filters = {}
    if role:
        filters["role"] = role
    if is_active is not None:
        filters["is_active"] = is_active
    if email_contains:
        filters["email_contains"] = email_contains
    if full_name_contains:
        filters["full_name_contains"] = full_name_contains

    service = UserService(db)
    paginated = await service.get_users(
        filters=filters,
        page=page,
        page_size=page_size
    )
    return success_response(data=paginated, message="Users retrieved")


@router.get("/{user_id}")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[UserResponse]:
    service = UserService(db)
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return success_response(data=user, message="User retrieved")


@router.put("/{user_id}")
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> SuccessResponse[UserResponse]:
    service = UserService(db)
    try:
        user = await service.update_user(user_id, data)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return success_response(data=user, message="User updated")
    except (UserNotFoundError, UserAlreadyExistsError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> None:
    service = UserService(db)
    deleted = await service.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return None