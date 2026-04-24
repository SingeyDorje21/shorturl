"""
Cleanup Service (port 8003)
-----------------------------
Background worker that periodically hard-deletes expired URL records so the
database doesn't grow unboundedly.  Also exposes a health + manual-trigger
endpoint for ops convenience.

Runs on its own schedule defined by CLEANUP_INTERVAL_SECONDS in config.
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from sqlalchemy.future import select
from sqlalchemy import delete

from shared.app.config import get_settings
from shared.app.db.session import init_db, async_session
from shared.app.db.models import URL
from shared.app.schemas import HealthResponse

settings = get_settings()

# ---------------------------------------------------------------------------
# Core cleanup logic
# ---------------------------------------------------------------------------

async def delete_expired_urls() -> int:
    """
    Delete all URL rows where active_till < now OR is_active is False.
    Returns the number of rows deleted.
    """
    now_utc = datetime.now(timezone.utc)
    async with async_session() as session:
        result = await session.execute(
            delete(URL).where(
                (URL.active_till < now_utc) | (URL.is_active == False)  # noqa: E712
            )
        )
        await session.commit()
        deleted = result.rowcount
        if deleted:
            print(f"[Cleanup] deleted {deleted} expired/inactive URL(s) at {now_utc.isoformat()}")
        return deleted


# ---------------------------------------------------------------------------
# Background scheduler
# ---------------------------------------------------------------------------

async def _scheduler():
    """Runs delete_expired_urls on a fixed interval."""
    while True:
        try:
            await delete_expired_urls()
        except Exception as exc:  # pragma: no cover
            print(f"[Cleanup] ERROR during scheduled run: {exc}")
        await asyncio.sleep(settings.CLEANUP_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Cleanup] initialising database...")
    await init_db()
    task = asyncio.create_task(_scheduler())
    print(f"[Cleanup] scheduler started — interval={settings.CLEANUP_INTERVAL_SECONDS}s")
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    print("[Cleanup] shut down")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Short URL — Cleanup Service",
    version=settings.VERSION,
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse, tags=["meta"])
async def health():
    return HealthResponse(service="cleanup", version=settings.VERSION)


@app.post("/run", tags=["ops"])
async def trigger_cleanup():
    """Manually trigger a cleanup run (useful for ops / testing)."""
    deleted = await delete_expired_urls()
    return {"deleted": deleted, "ran_at": datetime.now(timezone.utc).isoformat()}
