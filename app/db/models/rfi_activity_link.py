from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RFIActivityLink(Base):
    __tablename__ = "rfi_activity_links"

    rfi_id: Mapped[int] = mapped_column(ForeignKey("rfis.id", ondelete="CASCADE"), primary_key=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("schedule_activities.id", ondelete="CASCADE"), primary_key=True, index=True)

    link_source: Mapped[str] = mapped_column(String(30), nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    rfi: Mapped["RFI"] = relationship()
    activity: Mapped["ScheduleActivity"] = relationship()
