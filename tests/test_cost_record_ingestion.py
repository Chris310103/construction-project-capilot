from decimal import Decimal
from pathlib import Path

import pytest

from app.ingestion.cost_record_csv import cost_record_to_chunk, read_cost_rows
from app.schemas.cost_record_import import CostRecordCSVRow


def test_read_cost_csv(tmp_path: Path):
    csv_path = tmp_path / "cost.csv"
    csv_path.write_text(
        "cost_code,category,budget_amount,forecast_amount,currency,as_of_date\n"
        "23-100,HVAC,800000.00,850000.00,usd,2026-08-01\n"
        "23-100,HVAC,800000.00,820000.00,USD,2026-07-01\n",
        encoding="utf-8",
    )

    rows = read_cost_rows(csv_path)

    assert len(rows) == 2
    assert rows[0].currency == "USD"
    assert rows[0].budget_amount == Decimal("800000.00")
    assert rows[0].forecast_amount == Decimal("850000.00")


def test_cost_record_to_chunk():
    row = CostRecordCSVRow(
        cost_code="23-100",
        category="HVAC",
        description="MEP ductwork",
        budget_amount=Decimal("800000.00"),
        forecast_amount=Decimal("850000.00"),
        as_of_date="2026-08-01",
    )

    content = cost_record_to_chunk(row, 2)

    assert "CSV row: 2" in content
    assert "MEP ductwork" in content
    assert "Budget amount: 800000.00" in content
    assert "Forecast amount: 850000.00" in content


def test_invalid_cost_amount(tmp_path: Path):
    csv_path = tmp_path / "invalid.csv"
    csv_path.write_text(
        "cost_code,category,budget_amount,as_of_date\n"
        "23-100,HVAC,not_a_number,2026-08-01\n"
    )

    with pytest.raises(ValueError, match="Invalid CSV row"):
        read_cost_rows(csv_path)


def test_duplicate_cost_snapshot(tmp_path: Path):
    csv_path = tmp_path / "duplicate.csv"
    csv_path.write_text(
        "cost_code,category,as_of_date\n"
        "23-100,HVAC,2026-08-01\n"
        "23-100,HVAC,2026-08-01\n"
    )

    with pytest.raises(ValueError, match="Duplicate cost snapshot"):
        read_cost_rows(csv_path)


def test_invalid_currency():
    with pytest.raises(ValueError):
        CostRecordCSVRow(cost_code="23-100", category="HVAC", currency="USDD", as_of_date="2026-08-01")


def test_empty_cost_csv(tmp_path: Path):
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("cost_code,category,as_of_date\n")

    with pytest.raises(ValueError, match="CSV contains no valid Cost Record records"):
        read_cost_rows(csv_path)