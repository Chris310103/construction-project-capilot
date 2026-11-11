import csv
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import select

from app.db.models import Document, DocumentChunk, Project, RFI
from app.db.session import SessionLocal
from app.schemas.rfi_import import RFICSVRow


def rfi_to_chunk(row: RFICSVRow, row_number: int) -> str:
    parts = [
        "Document type: RFI",
        f"CSV row: {row_number}",
        f"RFI number: {row.rfi_number}",
        f"Subject: {row.subject}",
        f"Question: {row.question}",
        f"Status: {row.status}",
    ]

    if row.responsible_party:
        parts.append(f"Responsible party: {row.responsible_party}")

    if row.submitted_date:
        parts.append(f"Submitted date: {row.submitted_date}")

    if row.due_date:
        parts.append(f"Due date: {row.due_date}")

    if row.schedule_impact_days is not None:
        parts.append(f"Schedule impact: {row.schedule_impact_days} days")

    return "\n".join(parts)

def read_rfi_rows(csv_path: Path) -> list[RFICSVRow]:
    rows = []
    seen = set()

    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for line_number, raw_row in enumerate(reader, start=2):
            try:
                row = RFICSVRow.model_validate(raw_row)
            except ValidationError as exc:
                raise ValueError(f"Invalid CSV row {line_number}: {exc}") from exc

            if row.rfi_number in seen:
                raise ValueError(f"Duplicate RFI number: {row.rfi_number}")

            seen.add(row.rfi_number)
            rows.append(row)

    if not rows:
        raise ValueError("CSV contains no valid RFI records")

    return rows

def ingest_rfis(csv_path: Path, project_name: str) -> tuple[int, int]:
    rows = read_rfi_rows(csv_path)
    inserted = 0
    updated = 0

    with SessionLocal.begin() as db:
        project = db.scalar(select(Project).where(Project.name == project_name))

        if project is None:
            raise ValueError(f"Project not found: {project_name}")

        document = db.scalar(select(Document).where(Document.project_id == project.id, Document.file_name == csv_path.name))

        if document is None:
            document = Document(project_id=project.id, file_name=csv_path.name, document_type="RFI_CSV", file_path=str(csv_path))
            db.add(document)
            db.flush()

        for row in rows:
            rfi = db.scalar(select(RFI).where(RFI.project_id == project.id, RFI.rfi_number == row.rfi_number))

            if rfi is None:
                rfi = RFI(project_id=project.id, rfi_number=row.rfi_number, subject=row.subject, question=row.question)
                db.add(rfi)
                inserted += 1
            else:
                updated += 1

            rfi.source_document_id = document.id
            rfi.subject = row.subject
            rfi.question = row.question
            rfi.status = row.status
            rfi.responsible_party = row.responsible_party
            rfi.submitted_date = row.submitted_date
            rfi.due_date = row.due_date
            rfi.schedule_impact_days = row.schedule_impact_days

            existing_chunks = {chunk.chunk_index: chunk for chunk in db.scalars(select(DocumentChunk).where(DocumentChunk.document_id == document.id)).all()}

        for index, row in enumerate(rows):
            content = rfi_to_chunk(row, index + 2)
            chunk = existing_chunks.pop(index, None)

            if chunk is None:
                chunk = DocumentChunk(document_id=document.id, chunk_index=index, content=content, page_number=None)
                db.add(chunk)

            elif chunk.content != content:
                chunk.content = content
                chunk.embedding = None

        for stale_chunk in existing_chunks.values():
            db.delete(stale_chunk)

    return inserted, updated