from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

class Document(Base):
    __tablename__="documents"

    id: Mapped[int]=mapped_column(primary_key=True)
    project_id:Mapped[int]=mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    file_name:Mapped[str]=mapped_column(String(255), nullable=False)
    document_type:Mapped[str]=mapped_column(String(50), nullable=False)
    file_path:Mapped[str]=mapped_column(Text, nullable=False)
    uploaded_at:Mapped[datetime]=mapped_column(DateTime(timezone=True), server_default=func.now())

    project:Mapped["Project"]=relationship(back_populates="documents")
    chunks:Mapped[list["DocumentChunk"]]=relationship(back_populates="document", cascade="all, delete-orphan")