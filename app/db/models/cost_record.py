from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CostRecord(Base):
    __tablename__ = "cost_records"
    __table_args__ = (UniqueConstraint("project_id", "cost_code", "as_of_date", name="uq_cost_project_code_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    source_document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)

    cost_code: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    budget_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    committed_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    actual_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    forecast_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)

    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="cost_records")