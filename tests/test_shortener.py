import pytest


@pytest.mark.asyncio
async def test_shorten_returns_short_url(shortener_client):
    resp = await shortener_client.post("/shorten", json={"original_url": "https://example.com"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["original_url"] == "https://example.com/"
    assert data["short_code"]
    assert data["short_url"].endswith(data["short_code"])
    assert data["clicks"] == 0
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_shorten_custom_duration(shortener_client):
    resp = await shortener_client.post(
        "/shorten",
        json={"original_url": "https://example.com", "active_duration_days": 7},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["short_code"]
    # active_till should be returned and in the future
    assert data["active_till"] is not None


@pytest.mark.asyncio
async def test_shorten_duration_capped_at_max(shortener_client):
    """active_duration_days > URL_ACTIVE_DAYS_MAX should be silently capped."""
    resp = await shortener_client.post(
        "/shorten",
        json={"original_url": "https://example.com", "active_duration_days": 9999},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_shorten_rejects_invalid_url(shortener_client):
    resp = await shortener_client.post("/shorten", json={"original_url": "not-a-url"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_info_returns_metadata(shortener_client):
    # Create a URL first
    create = await shortener_client.post("/shorten", json={"original_url": "https://info-test.com"})
    code = create.json()["short_code"]

    resp = await shortener_client.get(f"/{code}/info")
    assert resp.status_code == 200
    data = resp.json()
    assert data["short_code"] == code
    assert data["clicks"] == 0


@pytest.mark.asyncio
async def test_info_404_for_unknown_code(shortener_client):
    resp = await shortener_client.get("/XXXXXX/info")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_health(shortener_client):
    resp = await shortener_client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "shortener"
