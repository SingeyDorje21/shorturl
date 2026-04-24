from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from shared.app.db.models import URL
from shared.app.db.session import get_session
from shared.app.schemas import URLCreate, URLInfo
from shared.app.services import base62_encode
from shared.app.config import get_settings

settings = get_settings()
router = APIRouter()


def _build_short_url(request: Request, short_code: str) -> str:
    # Return the gateway's public URL, not the internal service URL
    base = str(request.base_url).rstrip("/")
    return f"{base}/{short_code}"


@router.post("/shorten", response_model=URLInfo)
async def create_short_url(
    payload: URLCreate,
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    # Bug fix: honour any valid active_duration_days, not just values > 30
    active_days = settings.URL_ACTIVE_DAYS_DEFAULT
    if payload.active_duration_days is not None:
        active_days = min(payload.active_duration_days, settings.URL_ACTIVE_DAYS_MAX)

    new_url = URL(
        original_url=str(payload.original_url),
        is_active=True,
        clicks=0,
        active_till=datetime.now(timezone.utc) + timedelta(days=active_days),
    )
    db.add(new_url)
    await db.flush()  # get auto-generated id without committing

    generated_code = base62_encode(new_url.id)
    new_url.short_code = generated_code

    await db.commit()
    await db.refresh(new_url)

    return URLInfo(
        original_url=new_url.original_url,
        short_code=generated_code,
        is_active=new_url.is_active,
        clicks=new_url.clicks,
        short_url=_build_short_url(request, generated_code),
        active_till=new_url.active_till,
    )


@router.get("/{short_code}/info", response_model=URLInfo)
async def get_url_info(
    short_code: str,
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    result = await db.execute(select(URL).where(URL.short_code == short_code))
    db_url = result.scalar_one_or_none()

    if not db_url:
        raise HTTPException(status_code=404, detail="URL not found")
    if not db_url.short_code:
        raise HTTPException(status_code=500, detail="URL record is corrupt")

    return URLInfo(
        original_url=db_url.original_url,
        short_code=db_url.short_code,
        is_active=db_url.is_active,
        clicks=db_url.clicks,
        short_url=_build_short_url(request, db_url.short_code),
        active_till=db_url.active_till,
    )
