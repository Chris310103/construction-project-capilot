from pathlib import Path

import pytest

from app.ingestion.router import classify_document


def test_classify_rfi_csv(tmp_path: Path):
    path = tmp_path / "random.csv"
    path.write_text("rfi_number,subject,question,status\nRFI-100,HVAC,Check routing,open\n")
    assert classify_document(path) == "RFI_CSV"


def test_classify_cost_csv(tmp_path: Path):
    path = tmp_path / "unknown.csv"
    path.write_text("cost_code,category,as_of_date\n23-100,HVAC,2026-08-01\n")
    assert classify_document(path) == "COST_CSV"


def test_reject_unknown_columns(tmp_path: Path):
    path = tmp_path / "unknown.csv"
    path.write_text("name,value\nexample,123\n")

    with pytest.raises(ValueError, match="Cannot uniquely identify"):
        classify_document(path)


def test_reject_unsupported_file(tmp_path: Path):
    path = tmp_path / "notes.txt"
    path.write_text("Some construction notes")

    with pytest.raises(ValueError, match="Only PDF and CSV"):
        classify_document(path)