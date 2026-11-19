import re
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy import select

from app.db.models import Document, Project, RFI
from app.db.session import SessionLocal
from app.ingestion.pdf import extract_pdf_pages, ingest_pdf
from app.schemas.rfi_import import RFICSVRow


def looks_like_rfi_pdf(pdf_path: Path) -> bool:
    pages = extract_pdf_pages(pdf_path)
    first_page = pages[0][1]

    has_header = re.search(r"(?im)^REQUEST FOR INFORMATION[ \t]*$", first_page)
    has_number = re.search(r"(?im)^RFI Number:[ \t]*\S+", first_page)

    return bool(has_header and has_number)


def extract_rfi_fields(pdf_path: Path) -> tuple[RFICSVRow, str | None]:
    pages = extract_pdf_pages(pdf_path)
    text = "\n".join(content for _, content in pages)

    def get_field(label: str) -> str:
        match = re.search(rf"(?im)^[ \t]*{re.escape(label)}:[ \t]*(.*)$", text)
        return match.group(1).strip() if match else ""

    question_match = re.search(
        r"(?ims)^Question:[ \t]*(.*?)(?=^(?:Responsible Party|Response|Status|Subject|RFI Number|Project):|\Z)",
        text,
    )

    extracted = {
        "rfi_number": get_field("RFI Number"),
        "subject": get_field("Subject"),
        "status": get_field("Status"),
        "question": question_match.group(1).strip() if question_match else "",
        "responsible_party": get_field("Responsible Party") or None,
    }

    try:
        rfi_data = RFICSVRow.model_validate(extracted)
    except ValidationError as exc:
        raise ValueError(f"Invalid RFI PDF fields: {exc}") from exc

    return rfi_data, get_field("Project") or None


def ingest_rfi_pdf(pdf_path: Path, project_name: str) -> dict:
    rfi_data, declared_project = extract_rfi_fields(pdf_path)

    if declared_project and declared_project.casefold() != project_name.casefold():
        raise ValueError("PDF project name does not match the selected project")

    document_id, pages, changed = ingest_pdf(pdf_path, project_name)

    with SessionLocal.begin() as db:
        project = db.scalar(select(Project).where(Project.name == project_name))
        document = db.get(Document, document_id)

        if project is None or document is None:
            raise ValueError("Project or document not found")

        query = select(RFI).where(RFI.project_id == project.id, RFI.rfi_number == rfi_data.rfi_number)
        rfi = db.scalar(query)

        if rfi is None:
            rfi = RFI(
                project_id=project.id,
                rfi_number=rfi_data.rfi_number,
                subject=rfi_data.subject,
                question=rfi_data.question,
                status=rfi_data.status,
            )
            db.add(rfi)
            action = "inserted"
        else:
            action = "updated"

        rfi.subject = rfi_data.subject
        rfi.question = rfi_data.question
        rfi.status = rfi_data.status
        rfi.responsible_party = rfi_data.responsible_party
        rfi.source_document_id = document_id

        document.document_type = "RFI_PDF"

    return {
        "document_id": document_id,
        "pages": pages,
        "changed": changed,
        "rfi_number": rfi_data.rfi_number,
        "rfi_action": action,
    }