# app/modules/user/api/v1/endpoints/user.py
from datetime import timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession


from app.common.api.db import get_db
from app.common.dependencies.auth import get_current_user, require_role
from app.modules.user.services.user import UserService
from app.modules.user.schemas.base import Token, UserCreate, UserUpdate, UserResponse

from app.modules.user.models import User
from app.core.config import settings
from app.common.exceptions.user import (
    UserNotFoundError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
)

router = APIRouter()


# ------------------------------------------------------------------
# Authentication endpoints
# ------------------------------------------------------------------
@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate user with email and password. Returns JWT access token.
    """
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


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Register a new user (patient role by default, but can specify role if admin).
    """
    service = UserService(db)
    try:
        user = await service.create_user(data)
        return user
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a new access token using current user.
    """
    service = UserService(db)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = service.create_access_token(
        data={"sub": str(current_user.id), "role": current_user.role.value},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


# ------------------------------------------------------------------
# User CRUD endpoints (admin or self)
# ------------------------------------------------------------------
@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """
    Get information of the currently authenticated user.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update current user's own information.
    """
    service = UserService(db)
    try:
        updated = await service.update_user(current_user.id, data)
        return updated
    except (UserNotFoundError, UserAlreadyExistsError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/me/change-password", response_model=dict)
async def change_password(
    old_password: str,
    new_password: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Change current user's password.
    """
    service = UserService(db)
    success = await service.change_password(current_user.id, old_password, new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Incorrect old password")
    return {"message": "Password changed successfully"}


@router.get("/", response_model=List[UserResponse])
async def list_users(
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    email_contains: Optional[str] = Query(None),
    full_name_contains: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    List all users. Admin only.
    """
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
    users = await service.get_users(filters=filters, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = UserService(db)
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = UserService(db)
    try:
        user = await service.update_user(user_id, data)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except (UserNotFoundError, UserAlreadyExistsError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    service = UserService(db)
    deleted = await service.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return None