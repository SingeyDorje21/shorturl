from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.ext.asyncio.session import AsyncSession
from typing import AsyncGenerator

from shared.app.db import Base
from shared.app.db import models  # noqa: F401 — ensure models are registered
from shared.app.config import get_settings

settings = get_settings()

# SQLite does not support pool_size / max_overflow — only pass those for Postgres
_engine_kwargs: dict = {"echo": settings.DEBUG, "future": True}
if not settings.is_sqlite:
    _engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
    _engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
