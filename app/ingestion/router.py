import csv
from pathlib import Path

from app.ingestion.rfi_csv import ingest_rfis, read_rfi_rows
from app.ingestion.change_order_csv import ingest_change_orders, read_change_order_rows
from app.ingestion.daily_report_csv import ingest_daily_reports, read_daily_report_rows
from app.ingestion.schedule_csv import ingest_schedule, read_schedule_rows
from app.ingestion.cost_record_csv import ingest_cost_records, read_cost_rows
from app.ingestion.pdf import extract_pdf_pages, ingest_pdf
from app.ingestion.rfi_pdf import looks_like_rfi_pdf, extract_rfi_fields, ingest_rfi_pdf


CSV_HANDLERS = {
    "RFI_CSV": ({"rfi_number", "subject", "question", "status"}, read_rfi_rows, ingest_rfis),
    "CHANGE_ORDER_CSV": ({"change_order_number", "title", "status"}, read_change_order_rows, ingest_change_orders),
    "DAILY_REPORT_CSV": ({"report_date", "work_completed"}, read_daily_report_rows, ingest_daily_reports),
    "SCHEDULE_CSV": ({"activity_code", "name", "planned_start", "planned_finish", "status"}, read_schedule_rows, ingest_schedule),
    "COST_CSV": ({"cost_code", "category", "as_of_date"}, read_cost_rows, ingest_cost_records),
}


def classify_document(file_path: Path) -> str:
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        with file_path.open("rb") as file:
            if not file.read(5).startswith(b"%PDF-"):
                raise ValueError("Invalid PDF file")
        return "RFI_PDF" if looks_like_rfi_pdf(file_path) else "PDF"

    if suffix != ".csv":
        raise ValueError("Only PDF and CSV files are supported")

    with file_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.reader(file)
        headers = next(reader, [])

    columns = {column.strip() for column in headers}

    matches = [name for name, (required, _, _) in CSV_HANDLERS.items() if required.issubset(columns)]

    if len(matches) != 1:
        raise ValueError("Cannot uniquely identify CSV document type from columns")

    return matches[0]


def validate_document(file_path: Path, document_type: str) -> None:
    if document_type == "RFI_PDF":
        extract_rfi_fields(file_path)
        return
    if document_type == "PDF":
        extract_pdf_pages(file_path)
        return

    _, reader, _ = CSV_HANDLERS[document_type]
    reader(file_path)


def ingest_document(file_path: Path, project_name: str, document_type: str) -> dict:
    if document_type == "RFI_PDF":
        return ingest_rfi_pdf(file_path, project_name)
    if document_type == "PDF":
        document_id, pages, changed = ingest_pdf(file_path, project_name)
        return {"document_id": document_id, "pages": pages, "changed": changed}

    _, _, ingester = CSV_HANDLERS[document_type]
    inserted, updated = ingester(file_path, project_name)

    return {"inserted": inserted, "updated": updated}