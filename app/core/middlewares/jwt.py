# app/core/middleware.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError
from app.core.config import settings

class JWTAuthMiddleware(BaseHTTPMiddleware):
    EXCLUDED_PATHS = ["/api/v1/auth/login", "/api/v1/auth/register", "/docs", "/openapi.json", "/redoc"]
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS):
            return await call_next(request)
        
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid token")
        
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            request.state.user_id = payload.get("sub")  # store sa request state
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return await call_next(request)