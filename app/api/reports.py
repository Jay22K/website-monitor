from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import MonitoringResult, Website
from app.services.pdf import render_pdf_report
from app.services.report import SiteRow, generate_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/latest/pdf", response_class=Response)
async def download_latest_report_pdf(db: AsyncSession = Depends(get_db)):
    websites = (await db.execute(select(Website).order_by(Website.name))).scalars().all()
    if not websites:
        raise HTTPException(status_code=404, detail="No websites configured.")

    rows: list[SiteRow] = []
    for website in websites:
        result = await db.execute(
            select(MonitoringResult)
            .where(MonitoringResult.website_id == website.id)
            .order_by(MonitoringResult.checked_at.desc())
            .limit(1)
        )
        latest = result.scalar_one_or_none()
        if latest:
            rows.append(
                SiteRow(
                    name=website.name,
                    status=latest.status,
                    http_status_code=latest.http_status_code,
                    error_message=latest.error_message,
                )
            )
        else:
            rows.append(SiteRow(name=website.name, status="offline", http_status_code=None, error_message="No checks found"))

    report_body = generate_report(rows, report_date=date.today())
    pdf_bytes = render_pdf_report(report_body)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=website-report.pdf"},
    )
