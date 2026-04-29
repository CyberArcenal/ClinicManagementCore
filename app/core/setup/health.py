

from fastapi import FastAPI
from sqlalchemy import text
from app.core.database import SessionLocal


def setup_health_check(app:FastAPI) -> FastAPI:
    @app.get("/health/db")
    def check_db():
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            return {"status": "ok", "database": "connected"}
        except Exception as e:
            return {"status": "error", "detail": str(e)}
        finally:
            db.close()
    return app