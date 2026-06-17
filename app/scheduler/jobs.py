import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.db.models import Website, MonitoringResult
from app.services.checker import check_website
from app.services.report import generate_report, SiteRow
from app.services.email import send_report_email

logger = logging.getLogger(__name__)


async def _run_daily_checks() -> None:
    """
    Core coroutine:
    1. Fetch all tracked websites.
    2. Check each one concurrently.
    3. Persist results.
    4. Build & email the report.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Website))
        websites = result.scalars().all()

    if not websites:
        logger.info("No websites to check — skipping daily job.")
        return

    logger.info("Starting daily check for %d website(s)…", len(websites))

    # Check all websites concurrently
    checks = await asyncio.gather(
        *[check_website(site.url) for site in websites],
        return_exceptions=True,
    )

    rows: list[SiteRow] = []

    async with AsyncSessionLocal() as session:
        for site, check in zip(websites, checks):
            if isinstance(check, Exception):
                # Shouldn't normally happen — checker catches its own exceptions
                logger.error("Unexpected error checking %s: %s", site.url, check)
                continue

            record = MonitoringResult(
                website_id=site.id,
                status=check.status,
                http_status_code=check.http_status_code,
                response_time_ms=check.response_time_ms,
                error_message=check.error_message,
                checked_at=datetime.now(timezone.utc),
            )
            session.add(record)

            rows.append(
                SiteRow(
                    name=site.name,
                    status=check.status,
                    http_status_code=check.http_status_code,
                    error_message=check.error_message,
                )
            )

        await session.commit()

    logger.info("Results saved. Generating report…")
    report = generate_report(rows)
    logger.info("\n%s", report)

    # Send email (gracefully skipped if not configured)
    send_report_email(report)
    logger.info("Daily check complete.")


def daily_check_job() -> None:
    """
    Synchronous entry point called by APScheduler.
    Runs the async coroutine in a new event loop.
    """
    asyncio.run(_run_daily_checks())
