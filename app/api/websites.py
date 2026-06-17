from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import Website, MonitoringResult
from app.schemas.website import WebsiteCreate, WebsiteRead, CheckResponse
from app.services.checker import check_website

router = APIRouter(prefix="/websites", tags=["websites"])


# ──────────────────────────────────────────────
# POST /websites  — add a new website
# ──────────────────────────────────────────────
@router.post("/", response_model=WebsiteRead, status_code=status.HTTP_201_CREATED)
async def add_website(payload: WebsiteCreate, db: AsyncSession = Depends(get_db)):
    # Prevent duplicates
    existing = await db.execute(select(Website).where(Website.url == payload.url))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Website with URL '{payload.url}' already exists.",
        )

    site = Website(name=payload.name, url=payload.url)
    db.add(site)
    await db.commit()
    await db.refresh(site)
    return site


# ──────────────────────────────────────────────
# GET /websites  — list all websites
# ──────────────────────────────────────────────
@router.get("/", response_model=list[WebsiteRead])
async def list_websites(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Website).order_by(Website.created_at))
    return result.scalars().all()


# ──────────────────────────────────────────────
# POST /websites/{id}/check  — check one website now
# ──────────────────────────────────────────────
@router.post("/{website_id}/check", response_model=CheckResponse)
async def check_website_now(website_id: int, db: AsyncSession = Depends(get_db)):
    site = await db.get(Website, website_id)
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website not found.")

    result = await check_website(site.url)

    # Persist result
    record = MonitoringResult(
        website_id=site.id,
        status=result.status,
        http_status_code=result.http_status_code,
        response_time_ms=result.response_time_ms,
        error_message=result.error_message,
    )
    db.add(record)
    await db.commit()

    return CheckResponse(
        website=site.name,
        status=result.status,
        http_status_code=result.http_status_code,
        response_time_ms=result.response_time_ms,
        error_message=result.error_message,
    )


# ──────────────────────────────────────────────
# GET /websites/{id}/results  — history for one site
# ──────────────────────────────────────────────
@router.get("/{website_id}/results")
async def get_website_results(
    website_id: int, limit: int = 20, db: AsyncSession = Depends(get_db)
):
    site = await db.get(Website, website_id)
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website not found.")

    result = await db.execute(
        select(MonitoringResult)
        .where(MonitoringResult.website_id == website_id)
        .order_by(MonitoringResult.checked_at.desc())
        .limit(limit)
    )
    return result.scalars().all()
