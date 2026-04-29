from fastapi import Request
from app.core.database import SessionLocal
from starlette.middleware.base import BaseHTTPMiddleware


class DBSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        db = SessionLocal()
        request.state.db = db  # i-attach sa request
        try:
            response = await call_next(request)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        return response