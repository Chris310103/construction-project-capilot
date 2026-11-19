from pathlib import Path

import pytest

from app.ingestion.daily_report_csv import daily_report_to_chunk, read_daily_report_rows
from app.schemas.daily_report_import import DailyReportCSVRow


def test_read_daily_report_csv(tmp_path: Path):
    csv_path = tmp_path / "reports.csv"
    csv_path.write_text(
        "report_date,weather,workers_on_site,work_completed,issues,safety_incidents\n"
        "2026-08-02,Rain,42,Concrete slab completed,Delivery delayed,0\n",
        encoding="utf-8",
    )

    rows = read_daily_report_rows(csv_path)

    assert len(rows) == 1
    assert rows[0].workers_on_site == 42
    assert rows[0].safety_incidents == 0


def test_daily_report_to_chunk():
    row = DailyReportCSVRow(
        report_date="2026-08-03",
        work_completed="Installed HVAC ductwork",
        issues="Coordination required",
        safety_incidents=0,
    )

    content = daily_report_to_chunk(row, 2)

    assert "CSV row: 2" in content
    assert "Installed HVAC ductwork" in content
    assert "Coordination required" in content
    assert "Safety incidents: 0" in content


def test_invalid_worker_count(tmp_path: Path):
    csv_path = tmp_path / "invalid.csv"
    csv_path.write_text("report_date,work_completed,workers_on_site\n2026-08-02,Concrete,-5\n")

    with pytest.raises(ValueError, match="Invalid CSV row"):
        read_daily_report_rows(csv_path)


def test_duplicate_report_date(tmp_path: Path):
    csv_path = tmp_path / "duplicate.csv"
    csv_path.write_text(
        "report_date,work_completed\n"
        "2026-08-02,Concrete work\n"
        "2026-08-02,HVAC work\n"
    )

    with pytest.raises(ValueError, match="Duplicate report date"):
        read_daily_report_rows(csv_path)


def test_empty_daily_report_csv(tmp_path: Path):
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("report_date,work_completed\n")

    with pytest.raises(ValueError, match="CSV contains no valid Daily Report records"):
        read_daily_report_rows(csv_path)