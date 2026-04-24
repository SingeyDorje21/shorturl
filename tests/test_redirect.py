import pytest
from datetime import datetime, timedelta, timezone

from shared.app.db.models import URL
from tests.conftest import TestSession


async def _insert_url(original_url: str, short_code: str, active: bool = True, days: int = 30) -> URL:
    """Helper: directly insert a URL row for redirect tests."""
    url = URL(
        original_url=original_url,
        short_code=short_code,
        is_active=active,
        clicks=0,
        active_till=datetime.now(timezone.utc) + timedelta(days=days),
    )
    async with TestSession() as session:
        session.add(url)
        await session.commit()
    return url


@pytest.mark.asyncio
async def test_redirect_follows_url(redirect_client):
    await _insert_url("https://example.com", "testcode1")
    resp = await redirect_client.get("/testcode1", follow_redirects=False)
    assert resp.status_code == 307
    assert resp.headers["location"] == "https://example.com"


@pytest.mark.asyncio
async def test_redirect_increments_clicks(redirect_client):
    from sqlalchemy.future import select
    await _insert_url("https://clicks-test.com", "clickcode")

    # Hit the redirect twice
    await redirect_client.get("/clickcode", follow_redirects=False)
    await redirect_client.get("/clickcode", follow_redirects=False)

    async with TestSession() as session:
        result = await session.execute(select(URL).where(URL.short_code == "clickcode"))
        db_url = result.scalar_one()
        assert db_url.clicks == 2


@pytest.mark.asyncio
async def test_redirect_404_for_unknown(redirect_client):
    resp = await redirect_client.get("/doesnotexist", follow_redirects=False)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_redirect_410_for_expired(redirect_client):
    await _insert_url("https://expired.com", "expiredcode", days=-1)
    resp = await redirect_client.get("/expiredcode", follow_redirects=False)
    assert resp.status_code == 410


@pytest.mark.asyncio
async def test_redirect_410_for_inactive(redirect_client):
    await _insert_url("https://inactive.com", "inactivecode", active=False)
    resp = await redirect_client.get("/inactivecode", follow_redirects=False)
    assert resp.status_code == 410


@pytest.mark.asyncio
async def test_redirect_health(redirect_client):
    resp = await redirect_client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "redirect"
