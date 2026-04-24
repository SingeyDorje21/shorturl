"""
Shared test fixtures.
Each test gets a fresh in-memory SQLite database so tests are fully isolated.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from shared.app.db import Base
from shared.app.db import models  # noqa: F401 — register ORM models
from shared.app.db.session import get_session

# ── In-memory DB engine (per test session) ───────────────────────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
TestSession = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_session():
    async with TestSession() as session:
        yield session


# ── Create tables once before the test session ───────────────────────────────
@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ── Per-test DB rollback so tests don't bleed into each other ────────────────
@pytest_asyncio.fixture(autouse=True)
async def rollback_after_test():
    async with test_engine.begin() as conn:
        yield
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


# ── AsyncClient fixtures for each service ────────────────────────────────────

@pytest_asyncio.fixture
async def shortener_client():
    from shortener.app.main import app
    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def redirect_client():
    from redirect.app.main import app
    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def cleanup_client():
    from cleanup.app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
