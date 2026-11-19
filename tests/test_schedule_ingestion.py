from pathlib import Path

import pytest

from app.ingestion.schedule_csv import read_schedule_rows, schedule_to_chunk
from app.schemas.schedule_import import ScheduleCSVRow


def test_read_schedule_csv(tmp_path: Path):
    csv_path = tmp_path / "schedule.csv"
    csv_path.write_text(
        "activity_code,name,planned_start,planned_finish,forecast_finish,is_critical,status\n"
        "MEP-201,MEP Coordination,2026-08-01,2026-08-20,2026-08-25,true,in_progress\n",
        encoding="utf-8",
    )

    rows = read_schedule_rows(csv_path)

    assert len(rows) == 1
    assert rows[0].activity_code == "MEP-201"
    assert rows[0].is_critical is True
    assert rows[0].forecast_finish.isoformat() == "2026-08-25"


def test_schedule_to_chunk():
    row = ScheduleCSVRow(
        activity_code="MEP-201",
        name="MEP Coordination",
        description="Resolve electrical and HVAC conflicts",
        planned_start="2026-08-01",
        planned_finish="2026-08-20",
        forecast_finish="2026-08-25",
        is_critical=True,
        status="in_progress",
    )

    content = schedule_to_chunk(row, 2)

    assert "CSV row: 2" in content
    assert "MEP-201" in content
    assert "electrical and HVAC conflicts" in content
    assert "Critical activity: True" in content


def test_invalid_schedule_dates(tmp_path: Path):
    csv_path = tmp_path / "invalid.csv"
    csv_path.write_text(
        "activity_code,name,planned_start,planned_finish,status\n"
        "MEP-201,MEP Coordination,2026-08-20,2026-08-01,in_progress\n"
    )

    with pytest.raises(ValueError, match="Invalid CSV row"):
        read_schedule_rows(csv_path)


def test_duplicate_schedule_activity(tmp_path: Path):
    csv_path = tmp_path / "duplicate.csv"
    csv_path.write_text(
        "activity_code,name,planned_start,planned_finish,status\n"
        "MEP-201,MEP Coordination,2026-08-01,2026-08-20,in_progress\n"
        "MEP-201,MEP Coordination,2026-08-01,2026-08-20,in_progress\n"
    )

    with pytest.raises(ValueError, match="Duplicate activity code"):
        read_schedule_rows(csv_path)


def test_invalid_percent_complete():
    with pytest.raises(ValueError):
        ScheduleCSVRow(
            activity_code="MEP-201",
            name="MEP Coordination",
            planned_start="2026-08-01",
            planned_finish="2026-08-20",
            percent_complete=120,
            status="in_progress",
        )