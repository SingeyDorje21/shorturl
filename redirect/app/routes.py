from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from shared.app.db.models import URL
from shared.app.db.session import get_session

router = APIRouter()


def _as_utc(dt: datetime) -> datetime:
    """
    SQLite stores datetimes without timezone info (naive).
    We always write UTC, so treat any naive datetime as UTC on read-back.
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


# NOTE: /health must be registered BEFORE /{short_code} so it isn't
# captured by the wildcard route.

@router.get("/{short_code}")
async def forward_short_url(
    short_code: str,
    db: AsyncSession = Depends(get_session),
):
    result = await db.execute(select(URL).where(URL.short_code == short_code))
    db_url = result.scalar_one_or_none()

    if not db_url:
        raise HTTPException(status_code=404, detail="URL not found")

    now_utc = datetime.now(timezone.utc)
    active_till_utc = _as_utc(db_url.active_till)

    if not db_url.is_active or active_till_utc < now_utc:
        # Hard-delete expired records opportunistically on access
        await db.delete(db_url)
        await db.commit()
        raise HTTPException(status_code=410, detail="URL has expired or is inactive")

    # Increment click counter and record last access time
    db_url.clicks += 1
    db_url.last_opened_at = now_utc
    await db.commit()

    return RedirectResponse(url=db_url.original_url, status_code=307)
