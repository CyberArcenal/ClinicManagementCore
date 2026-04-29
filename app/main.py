from fastapi import FastAPI

from app.core.database import Base, SessionLocal, engine
from app.core.config import settings
from app.core.setup.health import setup_health_check
from app.core.setup.middlewares import setup_middleware
from app.core.setup.signals import setup_signals
from app.core.setup.router_discovery import discover_and_register_routers

def create_app() -> FastAPI:
    app = FastAPI(title="ClinicManagementCore", version="1.0.0")
    app = setup_middleware(app)
    
    # signals
    setup_signals()
    # Dynamic router registration – no need to manually list modules
    discover_and_register_routers(app, api_prefix="/api/v1")

    # Health check endpoints
    setup_health_check(app)
    

    # Development only – create tables
    if settings.ENV == "development":

        @app.on_event("startup")
        def init_tables():
            Base.metadata.create_all(bind=engine)

    return app


app = create_app()
