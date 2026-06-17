from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.checker import check_website
from app.schemas.website import CheckResponse

router = APIRouter(prefix="/demo", tags=["demo"])


class DemoCheckRequest(BaseModel):
    url: str


@router.post("/check-website", response_model=CheckResponse, summary="Demo check a URL")
async def demo_check_website(payload: DemoCheckRequest):
    if not payload.url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")

    result = await check_website(payload.url)
    return CheckResponse(
        website=payload.url,
        status=result.status,
        http_status_code=result.http_status_code,
        response_time_ms=result.response_time_ms,
        error_message=result.error_message,
    )
