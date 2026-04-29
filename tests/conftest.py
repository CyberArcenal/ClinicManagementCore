# tests/conftest.py
import asyncio
from app.common.api.db import get_db
from app.modules.user.schemas.base import UserCreate
from app.modules.user.services.user import UserService
import pytest
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.main import app
from app.core.database import Base
from app.core.config import settings

# ------------------------------------------------------------------
# Test database setup (in-memory SQLite)
# ------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
TestingAsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingAsyncSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db

# ------------------------------------------------------------------
# Fixture: database session (creates tables, yields session, drops)
# ------------------------------------------------------------------
@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestingAsyncSessionLocal() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# ------------------------------------------------------------------
# Fixture: test client (FastAPI TestClient)
# ------------------------------------------------------------------
@pytest.fixture(scope="function")
def client(db_session: AsyncSession) -> Generator[TestClient, None, None]:
    # The db_session fixture is already running; override is already set.
    with TestClient(app) as test_client:
        yield test_client

# ------------------------------------------------------------------
# Fixture: create a test user and return JWT token
# ------------------------------------------------------------------
@pytest.fixture
async def test_user_token(db_session: AsyncSession) -> str:
    user_service = UserService(db_session)
    user_data = UserCreate(
        email="testuser@example.com",
        full_name="Test User",
        password="testpass123",
        role="admin",  # or any role needed
        is_active=True
    )
    user = await user_service.create_user(user_data)
    # Generate token manually using service method
    token = user_service.create_access_token(data={"sub": str(user.id), "role": user.role.value})
    return token

# ------------------------------------------------------------------
# Fixture: authenticated client (pre‑populated Authorization header)
# ------------------------------------------------------------------
@pytest.fixture
async def auth_client(client: TestClient, test_user_token: str) -> TestClient:
    client.headers.update({"Authorization": f"Bearer {test_user_token}"})
    return client

# ------------------------------------------------------------------
# Optional: event loop fixture (for older pytest-asyncio)
# ------------------------------------------------------------------
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()