from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ScheduleCSVRow(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    activity_code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None

    planned_start: date
    planned_finish: date
    actual_start: date | None = None
    actual_finish: date | None = None
    forecast_finish: date | None = None

    percent_complete: Decimal | None = Field(default=None, ge=0, le=100, max_digits=5, decimal_places=2)
    total_float_days: int | None = None
    is_critical: bool | None = None
    status: Literal["not_started", "in_progress", "completed"]

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value):
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator(
        "description", "actual_start", "actual_finish", "forecast_finish",
        "percent_complete", "total_float_days", "is_critical", mode="before"
    )
    @classmethod
    def empty_as_none(cls, value):
        return None if isinstance(value, str) and not value.strip() else value

    @model_validator(mode="after")
    def validate_dates(self):
        if self.planned_finish < self.planned_start:
            raise ValueError("planned_finish must be on or after planned_start")

        if self.actual_start and self.actual_finish and self.actual_finish < self.actual_start:
            raise ValueError("actual_finish cannot be earlier than actual_start")

        if self.status == "completed" and self.actual_finish is None:
            raise ValueError("completed activities require actual_finish")

        return self