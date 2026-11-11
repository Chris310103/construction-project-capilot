from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ScheduleActivity(Base):
    __tablename__ = "schedule_activities"
    __table_args__ = (
        UniqueConstraint("project_id", "activity_code", name="uq_schedule_project_activity"),
        CheckConstraint("percent_complete >= 0 AND percent_complete <= 100", name="ck_schedule_percent_complete"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    source_document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)

    activity_code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    planned_start: Mapped[date] = mapped_column(Date, nullable=False)
    planned_finish: Mapped[date] = mapped_column(Date, nullable=False)
    actual_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_finish: Mapped[date | None] = mapped_column(Date, nullable=True)
    forecast_finish: Mapped[date | None] = mapped_column(Date, nullable=True)

    percent_complete: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    total_float_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_critical: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="not_started")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="schedule_activities")
