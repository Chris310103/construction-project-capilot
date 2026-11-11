from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DailyReport(Base):
    __tablename__ = "daily_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    source_document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)

    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    weather: Mapped[str | None] = mapped_column(String(100), nullable=True)
    workers_on_site: Mapped[int | None] = mapped_column(Integer, nullable=True)

    work_completed: Mapped[str] = mapped_column(Text, nullable=False)
    issues: Mapped[str | None] = mapped_column(Text, nullable=True)
    safety_incidents: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="daily_reports")
