from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.database import Base, engine
from app.core.config import settings
from app.core.middlewares.handlers import add_exception_handlers, override_openapi_schema
from app.core.setup.health import setup_health_check
from app.core.setup.middlewares import setup_middleware
from app.core.setup.openapi import validate_openapi
from app.core.setup.signals import setup_signals
from app.core.setup.router_discovery import discover_and_register_routers

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if settings.ENV == "development":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()

def create_app() -> FastAPI:
    app = FastAPI(
        title="ClinicManagementCore",
        version="1.0.0",
        lifespan=lifespan
    )
    setup_middleware(app)
    setup_signals()
    discover_and_register_routers(app, api_prefix="/api/v1")
    setup_health_check(app)
    add_exception_handlers(app)
    override_openapi_schema(app)
    validate_openapi(app)
    return app

app = create_app()