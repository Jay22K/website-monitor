from datetime import datetime, timezone
from sqlalchemy import Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Website(Base):
    __tablename__ = "websites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    results: Mapped[list["MonitoringResult"]] = relationship(
        "MonitoringResult", back_populates="website", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Website id={self.id} name={self.name!r} url={self.url!r}>"


class MonitoringResult(Base):
    __tablename__ = "monitoring_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    website_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # 'online' | 'offline'
    http_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    website: Mapped["Website"] = relationship("Website", back_populates="results")

    def __repr__(self) -> str:
        return f"<MonitoringResult id={self.id} website_id={self.website_id} status={self.status!r}>"
