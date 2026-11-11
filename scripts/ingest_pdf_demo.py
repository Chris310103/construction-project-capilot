from pathlib import Path

from sqlalchemy import select

from app.db.models import DocumentChunk
from app.db.session import SessionLocal
from app.ingestion.pdf import ingest_pdf


def main():
    pdf_path = Path("data/raw/RFI_040.pdf")

    document_id, page_count, changed = ingest_pdf(pdf_path, "Demo Boston Office Tower")

    print(f"Document ID: {document_id}")
    print(f"Extracted pages: {page_count}")
    print(f"Database updated: {changed}")

    with SessionLocal() as db:
        chunks = db.scalars(select(DocumentChunk).where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index)).all()

        for chunk in chunks:
            print(f"Page {chunk.page_number}: {chunk.content[:150]}")


if __name__ == "__main__":
    main()
