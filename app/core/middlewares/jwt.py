from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError
from app.core.config import settings

class JWTAuthMiddleware(BaseHTTPMiddleware):
    EXCLUDED_PATHS = [
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/health/db",
        "/",
    ]

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"status": False, "message": "Missing or invalid token", "data": None}
            )

        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            request.state.user_id = payload.get("sub")
        except JWTError:
            return JSONResponse(
                status_code=401,
                content={"status": False, "message": "Invalid token", "data": None}
            )

        return await call_next(request)