import csv
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import select

from app.db.models import DailyReport, Document, DocumentChunk, Project
from app.db.session import SessionLocal
from app.schemas.daily_report_import import DailyReportCSVRow


def read_daily_report_rows(csv_path: Path) -> list[DailyReportCSVRow]:
    rows = []
    seen_dates = set()

    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for line_number, raw_row in enumerate(reader, start=2):
            try:
                row = DailyReportCSVRow.model_validate(raw_row)
            except ValidationError as exc:
                raise ValueError(f"Invalid CSV row {line_number}: {exc}") from exc

            if row.report_date in seen_dates:
                raise ValueError(f"Duplicate report date: {row.report_date}")

            seen_dates.add(row.report_date)
            rows.append(row)

    if not rows:
        raise ValueError("CSV contains no valid Daily Report records")

    return rows

def daily_report_to_chunk(row: DailyReportCSVRow, row_number: int) -> str:
    parts = [
        "Document type: Daily Report",
        f"CSV row: {row_number}",
        f"Report date: {row.report_date}",
        f"Work completed: {row.work_completed}",
    ]

    if row.weather:
        parts.append(f"Weather: {row.weather}")

    if row.workers_on_site is not None:
        parts.append(f"Workers on site: {row.workers_on_site}")

    if row.issues:
        parts.append(f"Issues: {row.issues}")

    if row.safety_incidents is not None:
        parts.append(f"Safety incidents: {row.safety_incidents}")

    return "\n".join(parts)


def ingest_daily_reports(csv_path: Path, project_name: str) -> tuple[int, int]:
    rows = read_daily_report_rows(csv_path)
    inserted = 0
    updated = 0

    with SessionLocal.begin() as db:
        project = db.scalar(select(Project).where(Project.name == project_name))

        if project is None:
            raise ValueError(f"Project not found: {project_name}")

        query = select(Document).where(Document.project_id == project.id)
        query = query.where(Document.file_name == csv_path.name)
        document = db.scalar(query)

        if document is None:
            document = Document(
                project_id=project.id,
                file_name=csv_path.name,
                document_type="DAILY_REPORT_CSV",
                file_path=str(csv_path),
            )
            db.add(document)
            db.flush()

        for row in rows:
            query = select(DailyReport).where(DailyReport.project_id == project.id)
            query = query.where(DailyReport.source_document_id == document.id)
            query = query.where(DailyReport.report_date == row.report_date)
            report = db.scalar(query)

            if report is None:
                report = DailyReport(
                    project_id=project.id,
                    report_date=row.report_date,
                    work_completed=row.work_completed,
                )
                db.add(report)
                inserted += 1
            else:
                updated += 1

            report.source_document_id = document.id
            report.weather = row.weather
            report.workers_on_site = row.workers_on_site
            report.work_completed = row.work_completed
            report.issues = row.issues
            report.safety_incidents = row.safety_incidents

        existing = db.scalars(select(DocumentChunk).where(DocumentChunk.document_id == document.id)).all()
        existing_chunks = {chunk.chunk_index: chunk for chunk in existing}

        for index, row in enumerate(rows):
            content = daily_report_to_chunk(row, index + 2)
            chunk = existing_chunks.pop(index, None)

            if chunk is None:
                db.add(DocumentChunk(document_id=document.id, chunk_index=index, content=content))
            elif chunk.content != content:
                chunk.content = content
                chunk.embedding = None

        for stale_chunk in existing_chunks.values():
            db.delete(stale_chunk)

    return inserted, updated
