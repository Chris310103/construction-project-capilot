import csv
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import select

from app.db.models import Document, DocumentChunk, Project, ScheduleActivity
from app.db.session import SessionLocal
from app.schemas.schedule_import import ScheduleCSVRow


def read_schedule_rows(csv_path: Path) -> list[ScheduleCSVRow]:
    rows = []
    seen = set()

    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for line_number, raw_row in enumerate(reader, start=2):
            try:
                row = ScheduleCSVRow.model_validate(raw_row)
            except ValidationError as exc:
                raise ValueError(f"Invalid CSV row {line_number}: {exc}") from exc

            if row.activity_code in seen:
                raise ValueError(f"Duplicate activity code: {row.activity_code}")

            seen.add(row.activity_code)
            rows.append(row)

    if not rows:
        raise ValueError("CSV contains no valid Schedule records")

    return rows


def schedule_to_chunk(row: ScheduleCSVRow, row_number: int) -> str:
    parts = [
        "Document type: Schedule Activity",
        f"CSV row: {row_number}",
        f"Activity code: {row.activity_code}",
        f"Activity name: {row.name}",
        f"Status: {row.status}",
    ]

    if row.description:
        parts.append(f"Description: {row.description}")

    parts.append(f"Planned start: {row.planned_start}")
    parts.append(f"Planned finish: {row.planned_finish}")

    if row.forecast_finish:
        parts.append(f"Forecast finish: {row.forecast_finish}")

    if row.actual_finish:
        parts.append(f"Actual finish: {row.actual_finish}")

    if row.is_critical is not None:
        parts.append(f"Critical activity: {row.is_critical}")

    if row.total_float_days is not None:
        parts.append(f"Total float: {row.total_float_days} days")

    return "\n".join(parts)


def ingest_schedule(csv_path: Path, project_name: str) -> tuple[int, int]:
    rows = read_schedule_rows(csv_path)
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
                document_type="SCHEDULE_CSV",
                file_path=str(csv_path),
            )
            db.add(document)
            db.flush()

        for row in rows:
            query = select(ScheduleActivity).where(ScheduleActivity.project_id == project.id)
            query = query.where(ScheduleActivity.activity_code == row.activity_code)
            activity = db.scalar(query)

            if activity is None:
                activity = ScheduleActivity(
                    project_id=project.id,
                    activity_code=row.activity_code,
                    name=row.name,
                    planned_start=row.planned_start,
                    planned_finish=row.planned_finish,
                )
                db.add(activity)
                inserted += 1
            else:
                updated += 1

            activity.source_document_id = document.id
            activity.name = row.name
            activity.description = row.description
            activity.planned_start = row.planned_start
            activity.planned_finish = row.planned_finish
            activity.actual_start = row.actual_start
            activity.actual_finish = row.actual_finish
            activity.forecast_finish = row.forecast_finish
            activity.percent_complete = row.percent_complete
            activity.total_float_days = row.total_float_days
            activity.is_critical = row.is_critical
            activity.status = row.status

        existing = db.scalars(select(DocumentChunk).where(DocumentChunk.document_id == document.id)).all()
        existing_chunks = {chunk.chunk_index: chunk for chunk in existing}

        for index, row in enumerate(rows):
            content = schedule_to_chunk(row, index + 2)
            chunk = existing_chunks.pop(index, None)

            if chunk is None:
                db.add(DocumentChunk(document_id=document.id, chunk_index=index, content=content))
            elif chunk.content != content:
                chunk.content = content
                chunk.embedding = None

        for stale_chunk in existing_chunks.values():
            db.delete(stale_chunk)

    return inserted, updated