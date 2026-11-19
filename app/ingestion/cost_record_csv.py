import csv
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import select

from app.db.models import CostRecord, Document, DocumentChunk, Project
from app.db.session import SessionLocal
from app.schemas.cost_record_import import CostRecordCSVRow


def read_cost_rows(csv_path: Path) -> list[CostRecordCSVRow]:
    rows = []
    seen = set()

    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for line_number, raw_row in enumerate(reader, start=2):
            try:
                row = CostRecordCSVRow.model_validate(raw_row)
            except ValidationError as exc:
                raise ValueError(f"Invalid CSV row {line_number}: {exc}") from exc

            key = (row.cost_code, row.as_of_date)

            if key in seen:
                raise ValueError(f"Duplicate cost snapshot: {key}")

            seen.add(key)
            rows.append(row)

    if not rows:
        raise ValueError("CSV contains no valid Cost Record records")

    return rows

def cost_record_to_chunk(row: CostRecordCSVRow, row_number: int) -> str:
    parts = [
        "Document type: Cost Record",
        f"CSV row: {row_number}",
        f"Cost code: {row.cost_code}",
        f"Category: {row.category}",
        f"As of date: {row.as_of_date}",
        f"Currency: {row.currency}",
    ]

    if row.description:
        parts.append(f"Description: {row.description}")

    for field, label in [
        ("budget_amount", "Budget"),
        ("committed_amount", "Committed"),
        ("actual_amount", "Actual"),
        ("forecast_amount", "Forecast"),
    ]:
        value = getattr(row, field)

        if value is not None:
            parts.append(f"{label} amount: {value}")

    return "\n".join(parts)

def ingest_cost_records(csv_path: Path, project_name: str) -> tuple[int, int]:
    rows = read_cost_rows(csv_path)
    inserted = 0
    updated = 0

    with SessionLocal.begin() as db:
        project = db.scalar(select(Project).where(Project.name == project_name))

        if project is None:
            raise ValueError(f"Project not found: {project_name}")

        query = select(Document).where(Document.project_id == project.id, Document.file_name == csv_path.name)
        document = db.scalar(query)

        if document is None:
            document = Document(
                project_id=project.id,
                file_name=csv_path.name,
                document_type="COST_CSV",
                file_path=str(csv_path),
            )
            db.add(document)
            db.flush()

        for row in rows:
            query = select(CostRecord).where(CostRecord.project_id == project.id)
            query = query.where(CostRecord.cost_code == row.cost_code, CostRecord.as_of_date == row.as_of_date)
            record = db.scalar(query)

            if record is None:
                record = CostRecord(
                    project_id=project.id,
                    cost_code=row.cost_code,
                    category=row.category,
                    as_of_date=row.as_of_date,
                )
                db.add(record)
                inserted += 1
            else:
                updated += 1

            record.source_document_id = document.id
            record.category = row.category
            record.description = row.description
            record.budget_amount = row.budget_amount
            record.committed_amount = row.committed_amount
            record.actual_amount = row.actual_amount
            record.forecast_amount = row.forecast_amount
            record.currency = row.currency
            record.as_of_date = row.as_of_date

        existing = db.scalars(select(DocumentChunk).where(DocumentChunk.document_id == document.id)).all()
        existing_chunks = {chunk.chunk_index: chunk for chunk in existing}

        for index, row in enumerate(rows):
            content = cost_record_to_chunk(row, index + 2)
            chunk = existing_chunks.pop(index, None)

            if chunk is None:
                db.add(DocumentChunk(document_id=document.id, chunk_index=index, content=content))
            elif chunk.content != content:
                chunk.content = content
                chunk.embedding = None

        for stale_chunk in existing_chunks.values():
            db.delete(stale_chunk)

    return inserted, updated