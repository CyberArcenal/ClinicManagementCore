# app/modules/user/api/v1/__init__.py
from fastapi import APIRouter
from .endpoints.user import router as user_router

router = APIRouter()
router.include_router(user_router, prefix="/auth", tags=["Authentication"])