import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI

from app.db.database import engine, Base
from app.api.demo import router as demo_router
from app.api.reports import router as reports_router
from app.api.websites import router as websites_router
from app.scheduler.jobs import daily_check_job

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────
    logger.info("Creating database tables…")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Starting scheduler (daily check at 10:00 AM)…")
    scheduler.add_job(
        daily_check_job,
        trigger=CronTrigger(hour=10, minute=0),
        id="daily_website_check",
        replace_existing=True,
    )
    scheduler.start()

    yield

    # ── Shutdown ─────────────────────────────────────────
    logger.info("Shutting down scheduler…")
    scheduler.shutdown(wait=False)
    await engine.dispose()


app = FastAPI(
    title="Website Monitor",
    description="Track website uptime and receive daily email reports.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(websites_router)
app.include_router(reports_router)
app.include_router(demo_router)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}
