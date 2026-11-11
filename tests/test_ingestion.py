from pathlib import Path

import pymupdf
import pytest

from app.ingestion.pdf import extract_pdf_pages
from app.ingestion.rfi_csv import read_rfi_rows, rfi_to_chunk
from app.schemas.rfi_import import RFICSVRow


def test_rfi_to_chunk():
    row = RFICSVRow(rfi_number="RFI-100", subject="HVAC Conflict", question="HVAC duct conflicts with beam B17.", status="open", schedule_impact_days=0)

    content = rfi_to_chunk(row, 2)

    assert "CSV row: 2" in content
    assert "RFI number: RFI-100" in content
    assert "HVAC duct conflicts with beam B17." in content
    assert "Schedule impact: 0 days" in content


def test_read_rfi_csv(tmp_path: Path):
    csv_path = tmp_path / "rfis.csv"
    csv_path.write_text("rfi_number,subject,question,status,schedule_impact_days\nRFI-101,Mechanical Issue,Please revise duct routing, OPEN ,3\n", encoding="utf-8")

    rows = read_rfi_rows(csv_path)

    assert len(rows) == 1
    assert rows[0].rfi_number == "RFI-101"
    assert rows[0].status == "open"
    assert rows[0].schedule_impact_days == 3


def test_invalid_csv_row(tmp_path: Path):
    csv_path = tmp_path / "invalid.csv"
    csv_path.write_text("rfi_number,subject,question,status,schedule_impact_days\nRFI-102,HVAC Conflict,Check routing,open,-5\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid CSV row"):
        read_rfi_rows(csv_path)


def test_duplicate_rfi_number(tmp_path: Path):
    csv_path = tmp_path / "duplicate.csv"
    csv_path.write_text("rfi_number,subject,question,status\nRFI-103,Issue A,Question A,open\nRFI-103,Issue B,Question B,closed\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate RFI number"):
        read_rfi_rows(csv_path)


def test_extract_pdf_pages(tmp_path: Path):
    pdf_path = tmp_path / "test.pdf"

    with pymupdf.open() as pdf:
        page1 = pdf.new_page()
        page1.insert_text((72, 72), "RFI-104: HVAC Conflict")

        page2 = pdf.new_page()
        page2.insert_text((72, 72), "Please provide revised coordination drawings.")

        pdf.save(str(pdf_path))

    pages = extract_pdf_pages(pdf_path)

    assert len(pages) == 2
    assert pages[0][0] == 1
    assert pages[1][0] == 2
    assert "HVAC Conflict" in pages[0][1]
    assert "revised coordination drawings" in pages[1][1]


def test_empty_pdf(tmp_path: Path):
    pdf_path = tmp_path / "empty.pdf"

    with pymupdf.open() as pdf:
        pdf.new_page()
        pdf.save(str(pdf_path))

    with pytest.raises(ValueError, match="No extractable text"):
        extract_pdf_pages(pdf_path)
