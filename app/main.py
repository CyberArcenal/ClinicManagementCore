from fastapi import FastAPI
from app.api.v1.endpoints import patients
from app.core.database import Base, engine
from app.core.config import settings
from sqlalchemy import text
from app.core.database import SessionLocal

app = FastAPI()
# Create database tables (for development only, use Alembic in production)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Clinic Management API")

# Include routers
app.include_router(patients.router, prefix="/api/v1", tags=["patients"])



@app.get("/health/db")
def check_db():
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}