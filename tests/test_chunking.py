import pytest

from app.ingestion.chunking import split_text
from app.ingestion.pdf import chunk_pdf_pages


def test_short_text():
    chunks = split_text("HVAC duct conflicts with beam B17.")

    assert len(chunks) == 1
    assert chunks[0] == "HVAC duct conflicts with beam B17."


def test_long_text_overlap():
    text = "A" * 2000
    chunks = split_text(text, chunk_size=800, chunk_overlap=120)

    assert len(chunks) > 1
    assert all(len(chunk) <= 800 for chunk in chunks)
    assert chunks[0][-120:] == chunks[1][:120]


def test_pdf_page_numbers():
    pages = [(1, "A" * 1000), (2, "Electrical coordination issue.")]
    chunks = chunk_pdf_pages(pages, chunk_size=400, chunk_overlap=80)

    assert len(chunks) == 4
    assert [page for page, content in chunks] == [1, 1, 1, 2]


def test_invalid_chunk_settings():
    with pytest.raises(ValueError):
        split_text("Hello", chunk_size=0)

    with pytest.raises(ValueError):
        split_text("Hello", chunk_size=100, chunk_overlap=100)