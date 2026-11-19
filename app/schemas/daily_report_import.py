from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DailyReportCSVRow(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    report_date: date
    weather: str | None = None
    workers_on_site: int | None = Field(default=None, ge=0)
    work_completed: str = Field(min_length=1)
    issues: str | None = None
    safety_incidents: int | None = Field(default=None, ge=0)

    @field_validator("weather", "workers_on_site", "issues", "safety_incidents", mode="before")
    @classmethod
    def empty_as_none(cls, value):
        return None if isinstance(value, str) and not value.strip() else value