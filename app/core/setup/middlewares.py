from fastapi import FastAPI
from app.core.components.cors import ALLOWED_HOST, ALLOWED_METHOD, ALLOWED_HEADERS
from app.core.middlewares.logging import LoggingMiddleware
from app.core.middlewares.request_id import RequestIDMiddleware
from app.core.middlewares.jwt import JWTAuthMiddleware
from fastapi.middleware.cors import CORSMiddleware


def setup_middleware(app: FastAPI) -> FastAPI:
    # CORS – pinakalabas
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_HOST,
        allow_credentials=True,
        allow_methods=ALLOWED_METHOD,
        allow_headers=ALLOWED_HEADERS,
    )
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(JWTAuthMiddleware)
    return app
