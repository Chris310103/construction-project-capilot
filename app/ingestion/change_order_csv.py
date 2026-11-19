import csv
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import select

from app.db.models import ChangeOrder, Document, DocumentChunk, Project
from app.db.session import SessionLocal
from app.schemas.change_order_import import ChangeOrderCSVRow


def read_change_order_rows(csv_path: Path) -> list[ChangeOrderCSVRow]:
    rows = []
    seen = set()

    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for line_number, raw_row in enumerate(reader, start=2):
            try:
                row = ChangeOrderCSVRow.model_validate(raw_row)
            except ValidationError as exc:
                raise ValueError(f"Invalid CSV row {line_number}: {exc}") from exc

            if row.change_order_number in seen:
                raise ValueError(f"Duplicate Change Order number: {row.change_order_number}")

            seen.add(row.change_order_number)
            rows.append(row)

    if not rows:
        raise ValueError("CSV contains no valid Change Order records")

    return rows


def change_order_to_chunk(row: ChangeOrderCSVRow, row_number: int) -> str:
    parts = [
        "Document type: Change Order",
        f"CSV row: {row_number}",
        f"Change Order number: {row.change_order_number}",
        f"Title: {row.title}",
        f"Status: {row.status}",
    ]

    if row.description:
        parts.append(f"Description: {row.description}")

    if row.amount is not None:
        parts.append(f"Amount: {row.amount}")

    if row.schedule_impact_days is not None:
        parts.append(f"Schedule impact: {row.schedule_impact_days} days")

    return "\n".join(parts)


def ingest_change_orders(csv_path: Path, project_name: str) -> tuple[int, int]:
    rows = read_change_order_rows(csv_path)
    inserted = 0
    updated = 0

    with SessionLocal.begin() as db:
        project = db.scalar(select(Project).where(Project.name == project_name))

        if project is None:
            raise ValueError(f"Project not found: {project_name}")

        document_query = select(Document).where(Document.project_id == project.id)
        document_query = document_query.where(Document.file_name == csv_path.name)
        document = db.scalar(document_query)

        if document is None:
            document = Document(
                project_id=project.id,
                file_name=csv_path.name,
                document_type="CHANGE_ORDER_CSV",
                file_path=str(csv_path),
            )
            db.add(document)
            db.flush()

        for row in rows:
            query = select(ChangeOrder).where(ChangeOrder.project_id == project.id)
            query = query.where(ChangeOrder.change_order_number == row.change_order_number)
            change_order = db.scalar(query)

            if change_order is None:
                change_order = ChangeOrder(
                    project_id=project.id,
                    change_order_number=row.change_order_number,
                    title=row.title,
                )
                db.add(change_order)
                inserted += 1
            else:
                updated += 1

            change_order.source_document_id = document.id
            change_order.title = row.title
            change_order.description = row.description
            change_order.status = row.status
            change_order.amount = row.amount
            change_order.schedule_impact_days = row.schedule_impact_days
            change_order.submitted_date = row.submitted_date
            change_order.approved_date = row.approved_date

        existing = db.scalars(select(DocumentChunk).where(DocumentChunk.document_id == document.id)).all()
        existing_chunks = {chunk.chunk_index: chunk for chunk in existing}

        for index, row in enumerate(rows):
            content = change_order_to_chunk(row, index + 2)
            chunk = existing_chunks.pop(index, None)

            if chunk is None:
                db.add(DocumentChunk(document_id=document.id, chunk_index=index, content=content))
            elif chunk.content != content:
                chunk.content = content
                chunk.embedding = None

        for stale_chunk in existing_chunks.values():
            db.delete(stale_chunk)

    return inserted, updated