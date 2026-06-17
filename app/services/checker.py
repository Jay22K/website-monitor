import time
from dataclasses import dataclass

import httpx


@dataclass
class CheckResult:
    status: str                    # 'online' | 'offline'
    http_status_code: int | None
    response_time_ms: float | None
    error_message: str | None


async def check_website(url: str, timeout: float = 10.0) -> CheckResult:
    """
    Perform a single HTTP GET against *url*.

    Returns a CheckResult with status='online' if we receive any HTTP
    response (even a 5xx), and status='offline' on network-level failures
    (DNS error, connection refused, timeout, etc.).
    """
    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            response = await client.get(url)
        elapsed_ms = (time.perf_counter() - start) * 1000
        return CheckResult(
            status="online",
            http_status_code=response.status_code,
            response_time_ms=round(elapsed_ms, 2),
            error_message=None,
        )
    except httpx.TimeoutException:
        return CheckResult(
            status="offline",
            http_status_code=None,
            response_time_ms=None,
            error_message="Connection timeout",
        )
    except httpx.ConnectError as exc:
        return CheckResult(
            status="offline",
            http_status_code=None,
            response_time_ms=None,
            error_message=f"Connection error: {exc}",
        )
    except Exception as exc:
        return CheckResult(
            status="offline",
            http_status_code=None,
            response_time_ms=None,
            error_message=str(exc),
        )
