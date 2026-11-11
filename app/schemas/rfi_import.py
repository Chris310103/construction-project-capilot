from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RFICSVRow(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    rfi_number: str = Field(min_length=1, max_length=50)
    subject: str = Field(min_length=1, max_length=255)
    question: str = Field(min_length=1)
    status: Literal["open", "closed", "pending"]
    responsible_party: str | None = None
    submitted_date: date | None = None
    due_date: date | None = None
    schedule_impact_days: int | None = Field(default=None, ge=0)

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value):
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("responsible_party", "submitted_date", "due_date", "schedule_impact_days", mode="before")
    @classmethod
    def empty_as_none(cls, value):
        return None if isinstance(value, str) and not value.strip() else value