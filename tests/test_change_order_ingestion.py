from decimal import Decimal
from pathlib import Path

import pytest

from app.ingestion.change_order_csv import change_order_to_chunk, read_change_order_rows
from app.schemas.change_order_import import ChangeOrderCSVRow


def test_read_change_order_csv(tmp_path: Path):
    csv_path = tmp_path / "change_orders.csv"

    csv_text = """change_order_number,title,description,status,amount,schedule_impact_days,submitted_date,approved_date
CO-101,Additional HVAC,Install additional HVAC fans, APPROVED ,85000.00,2,2026-07-08,2026-07-17
CO-102,Exterior Revision,Revise facade materials,pending,30000.00,,2026-07-19,
"""
    csv_path.write_text(csv_text, encoding="utf-8")

    rows = read_change_order_rows(csv_path)

    assert len(rows) == 2
    assert rows[0].change_order_number == "CO-101"
    assert rows[0].status == "approved"
    assert rows[0].amount == Decimal("85000.00")
    assert rows[1].schedule_impact_days is None
    assert rows[1].approved_date is None


def test_change_order_to_chunk():
    row = ChangeOrderCSVRow(
        change_order_number="CO-101",
        title="Additional HVAC",
        description="Install additional HVAC fans",
        status="approved",
        amount=Decimal("85000.00"),
        schedule_impact_days=2,
    )

    content = change_order_to_chunk(row, 2)

    assert "CSV row: 2" in content
    assert "CO-101" in content
    assert "Install additional HVAC fans" in content
    assert "Amount: 85000.00" in content
    assert "Schedule impact: 2 days" in content


def test_invalid_amount(tmp_path: Path):
    csv_path = tmp_path / "invalid.csv"

    csv_text = """change_order_number,title,status,amount
CO-103,HVAC Change,approved,not_a_number
"""
    csv_path.write_text(csv_text, encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid CSV row"):
        read_change_order_rows(csv_path)


def test_invalid_status(tmp_path: Path):
    csv_path = tmp_path / "invalid_status.csv"

    csv_text = """change_order_number,title,status,amount
CO-104,HVAC Change,unknown,50000.00
"""
    csv_path.write_text(csv_text, encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid CSV row"):
        read_change_order_rows(csv_path)


def test_duplicate_change_order(tmp_path: Path):
    csv_path = tmp_path / "duplicate.csv"

    csv_text = """change_order_number,title,status
CO-105,Change A,approved
CO-105,Change B,pending
"""
    csv_path.write_text(csv_text, encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate Change Order number"):
        read_change_order_rows(csv_path)


def test_empty_change_order_csv(tmp_path: Path):
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("change_order_number,title,status\n", encoding="utf-8")

    with pytest.raises(ValueError, match="CSV contains no valid Change Order records"):
        read_change_order_rows(csv_path)