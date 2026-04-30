import logging
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.openapi.utils import get_openapi

logger = logging.getLogger(__name__)

def add_exception_handlers(app: FastAPI):
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        # Log HTTP exceptions (e.g., 404, 401) with level WARNING
        logger.warning(f"HTTP {exc.status_code}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"status": False, "message": exc.detail, "data": None}
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        message = ", ".join([f"{err['loc'][-1]}: {err['msg']}" for err in errors])
        logger.warning(f"Validation error: {message}")
        return JSONResponse(
            status_code=422,
            content={"status": False, "message": message, "data": None}
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        # Log the full traceback for any unexpected error
        logger.error(f"Unhandled exception: {exc}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"status": False, "message": "Internal server error", "data": None}
        )

def override_openapi_schema(app: FastAPI):
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            routes=app.routes,
        )
        # Replace default 422 response schema with your custom one
        for path in openapi_schema["paths"].values():
            for method in path.values():
                if "responses" in method and "422" in method["responses"]:
                    method["responses"]["422"] = {
                        "description": "Validation Error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "status": {"type": "boolean", "example": False},
                                        "message": {"type": "string"},
                                        "data": {"type": "null"}
                                    },
                                    "required": ["status", "message", "data"]
                                }
                            }
                        }
                    }
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    app.openapi = custom_openapi