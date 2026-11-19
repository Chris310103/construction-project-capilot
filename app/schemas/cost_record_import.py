from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CostRecordCSVRow(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    cost_code: str = Field(min_length=1, max_length=50)
    category: str = Field(min_length=1, max_length=100)
    description: str | None = None

    budget_amount: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    committed_amount: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    actual_amount: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    forecast_amount: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)

    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    as_of_date: date

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value):
        return value.strip().upper() if isinstance(value, str) else value

    @field_validator(
        "description", "budget_amount", "committed_amount",
        "actual_amount", "forecast_amount", mode="before"
    )
    @classmethod
    def empty_as_none(cls, value):
        return None if isinstance(value, str) and not value.strip() else value