from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChangeOrderCSVRow(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    change_order_number: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    status: Literal["pending", "approved", "rejected"]
    amount: Decimal | None = Field(default=None, max_digits=14, decimal_places=2)
    schedule_impact_days: int | None = None
    submitted_date: date | None = None
    approved_date: date | None = None

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value):
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("description", "amount", "schedule_impact_days", "submitted_date", "approved_date", mode="before")
    @classmethod
    def empty_as_none(cls, value):
        return None if isinstance(value, str) and not value.strip() else value