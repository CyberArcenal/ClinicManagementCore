from fastapi import FastAPI
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

def setup_health_check(app: FastAPI) -> FastAPI:
    @app.get("/health/db")
    async def check_db():
        async with AsyncSessionLocal() as db:
            try:
                await db.execute(text("SELECT 1"))
                return {"status": "ok", "database": "connected"}
            except Exception as e:
                return {"status": "error", "detail": str(e)}
    return app