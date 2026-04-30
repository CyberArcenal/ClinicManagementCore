from fastapi import APIRouter
from .endpoints.user import router as user_router

router = APIRouter()
router.include_router(user_router, prefix="/auth", tags=["Authentication"])