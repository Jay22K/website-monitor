"""Unit tests for the website checker service."""
import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.checker import check_website, CheckResult


@pytest.mark.asyncio
async def test_check_website_online():
    """A 200 response is classified as online."""
    mock_response = MagicMock()
    mock_response.status_code = 200

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("app.services.checker.httpx.AsyncClient", return_value=mock_client):
        result = await check_website("https://example.com")

    assert result.status == "online"
    assert result.http_status_code == 200
    assert result.response_time_ms is not None
    assert result.error_message is None


@pytest.mark.asyncio
async def test_check_website_timeout():
    """A timeout is classified as offline with the correct error message."""
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timed out"))

    with patch("app.services.checker.httpx.AsyncClient", return_value=mock_client):
        result = await check_website("https://example.com")

    assert result.status == "offline"
    assert result.http_status_code is None
    assert result.response_time_ms is None
    assert result.error_message == "Connection timeout"


@pytest.mark.asyncio
async def test_check_website_connection_error():
    """A connection error is classified as offline."""
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("refused"))

    with patch("app.services.checker.httpx.AsyncClient", return_value=mock_client):
        result = await check_website("https://down-site.com")

    assert result.status == "offline"
    assert "Connection error" in result.error_message


@pytest.mark.asyncio
async def test_check_website_server_error_is_online():
    """A 503 response still counts as online (we got a response)."""
    mock_response = MagicMock()
    mock_response.status_code = 503

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("app.services.checker.httpx.AsyncClient", return_value=mock_client):
        result = await check_website("https://degraded-site.com")

    assert result.status == "online"
    assert result.http_status_code == 503
