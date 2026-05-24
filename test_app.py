import re

import pytest
from httpx import ASGITransport, AsyncClient

from app import app, store


@pytest.fixture(autouse=True)
def clear_store():
    store.clear()
    yield
    store.clear()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


@pytest.mark.asyncio
async def test_ac1_create_short_url(client):
    original = "https://example.com/very/long/path"
    resp = await client.post("/api/shorten", json={"url": original})
    assert resp.status_code == 201
    body = resp.json()
    assert set(body.keys()) == {"shortCode", "shortUrl", "originalUrl"}
    assert body["originalUrl"] == original
    assert re.fullmatch(r"[A-Za-z0-9]{6}", body["shortCode"])
    assert body["shortUrl"].endswith(f"/{body['shortCode']}")


@pytest.mark.asyncio
async def test_ac2_redirect_increments_click_count(client):
    original = "https://example.com/page"
    create = await client.post("/api/shorten", json={"url": original})
    code = create.json()["shortCode"]

    resp = await client.get(f"/{code}", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["location"] == original

    stats = await client.get(f"/api/stats/{code}")
    assert stats.json()["clickCount"] == 1

    await client.get(f"/{code}", follow_redirects=False)
    stats = await client.get(f"/api/stats/{code}")
    assert stats.json()["clickCount"] == 2


@pytest.mark.asyncio
async def test_ac3_redirect_not_found(client):
    resp = await client.get("/abcXYZ", follow_redirects=False)
    assert resp.status_code == 404
    assert resp.json() == {"error": "Short code not found"}


@pytest.mark.asyncio
async def test_ac4_get_click_count(client):
    original = "https://example.com/foo"
    create = await client.post("/api/shorten", json={"url": original})
    code = create.json()["shortCode"]

    resp = await client.get(f"/api/stats/{code}")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"shortCode": code, "clickCount": 0, "originalUrl": original}

    missing = await client.get("/api/stats/nope12")
    assert missing.status_code == 404
    assert missing.json() == {"error": "Short code not found"}


@pytest.mark.asyncio
async def test_ac5_health_check(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", body["timestamp"])


@pytest.mark.asyncio
async def test_ac6_invalid_url(client):
    for payload in [{}, {"url": ""}, {"url": "not-a-url"}, {"url": "ftp://x.com"}]:
        resp = await client.post("/api/shorten", json=payload)
        assert resp.status_code == 400
        assert resp.json() == {"error": "Invalid URL provided"}

    resp = await client.post(
        "/api/shorten",
        content="not json",
        headers={"content-type": "application/json"},
    )
    assert resp.status_code == 400
    assert resp.json() == {"error": "Invalid URL provided"}
