from fastapi import APIRouter
from .endpoints.room import router as room_router

router = APIRouter()
router.include_router(room_router, prefix="/rooms", tags=["Rooms"])