from datetime import datetime
from pydantic import BaseModel, HttpUrl, field_validator


# ---------- Website ----------

class WebsiteCreate(BaseModel):
    name: str
    url: str

    @field_validator("url")
    @classmethod
    def url_must_have_scheme(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class WebsiteRead(BaseModel):
    id: int
    name: str
    url: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------- MonitoringResult ----------

class MonitoringResultRead(BaseModel):
    id: int
    website_id: int
    status: str
    http_status_code: int | None
    response_time_ms: float | None
    error_message: str | None
    checked_at: datetime

    model_config = {"from_attributes": True}


# ---------- Check Response ----------

class CheckResponse(BaseModel):
    website: str
    status: str
    http_status_code: int | None = None
    response_time_ms: float | None = None
    error_message: str | None = None
