from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime, String, Text, func

from app.db.base import Base

class Project(Base):
    __tablename__="projects"

    id:Mapped[int]=mapped_column(primary_key=True)
    name:Mapped[str]=mapped_column(String(200), nullable=False)
    description:Mapped[str|None]=mapped_column(Text, nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True), server_default=func.now())

    documents: Mapped[list["Document"]]=relationship(back_populates="project", cascade="all, delete-orphan")
    rfis: Mapped[list["RFI"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    change_orders: Mapped[list["ChangeOrder"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    daily_reports: Mapped[list["DailyReport"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    schedule_activities: Mapped[list["ScheduleActivity"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    cost_records: Mapped[list["CostRecord"]] = relationship(back_populates="project", cascade="all, delete-orphan")