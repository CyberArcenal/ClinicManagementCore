from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Pre-processing
        print(f">>> {request.method} {request.url.path}")
        
        # Call next
        response = await call_next(request)
        
        # Post-processing
        print(f"<<< Status: {response.status_code}")
        return response