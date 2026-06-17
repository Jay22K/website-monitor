"""
API integration tests.

Uses an in-memory SQLite database so no real Postgres instance is needed.
The checker service is mocked so no real HTTP requests are made.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.db.database import Base, get_db
from app.services.checker import CheckResult

# ── In-memory SQLite for tests ────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
async def setup_db():
    """Create tables before each test, drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_add_website(client):
    resp = await client.post("/websites/", json={"name": "Google", "url": "https://google.com"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Google"
    assert data["url"] == "https://google.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_add_duplicate_website(client):
    await client.post("/websites/", json={"name": "Google", "url": "https://google.com"})
    resp = await client.post("/websites/", json={"name": "Google2", "url": "https://google.com"})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_list_websites_empty(client):
    resp = await client.get("/websites/")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_websites(client):
    await client.post("/websites/", json={"name": "Google", "url": "https://google.com"})
    await client.post("/websites/", json={"name": "GitHub", "url": "https://github.com"})
    resp = await client.get("/websites/")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


@pytest.mark.asyncio
async def test_check_website_online(client):
    add = await client.post("/websites/", json={"name": "Google", "url": "https://google.com"})
    website_id = add.json()["id"]

    mock_result = CheckResult(
        status="online", http_status_code=200, response_time_ms=55.3, error_message=None
    )
    with patch("app.api.websites.check_website", new=AsyncMock(return_value=mock_result)):
        resp = await client.post(f"/websites/{website_id}/check")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "online"
    assert data["http_status_code"] == 200
    assert data["response_time_ms"] == 55.3


@pytest.mark.asyncio
async def test_check_website_offline(client):
    add = await client.post("/websites/", json={"name": "Down", "url": "https://down.example.com"})
    website_id = add.json()["id"]

    mock_result = CheckResult(
        status="offline", http_status_code=None, response_time_ms=None,
        error_message="Connection timeout"
    )
    with patch("app.api.websites.check_website", new=AsyncMock(return_value=mock_result)):
        resp = await client.post(f"/websites/{website_id}/check")

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "offline"
    assert data["error_message"] == "Connection timeout"


@pytest.mark.asyncio
async def test_check_nonexistent_website(client):
    resp = await client.post("/websites/9999/check")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_download_latest_report_pdf(client):
    add = await client.post("/websites/", json={"name": "Example", "url": "https://example.com"})
    website_id = add.json()["id"]

    mock_result = CheckResult(
        status="online", http_status_code=200, response_time_ms=45.7, error_message=None
    )
    with patch("app.api.websites.check_website", new=AsyncMock(return_value=mock_result)):
        resp = await client.post(f"/websites/{website_id}/check")
    assert resp.status_code == 200

    report_resp = await client.get("/reports/latest/pdf")
    assert report_resp.status_code == 200
    assert report_resp.headers["content-type"] == "application/pdf"
    assert report_resp.headers["content-disposition"] == "attachment; filename=website-report.pdf"
    assert report_resp.content.startswith(b"%PDF")
