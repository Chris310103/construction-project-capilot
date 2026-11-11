from pathlib import Path

import pymupdf
from sqlalchemy import delete, select

from app.db.models import Document, DocumentChunk, Project
from app.db.session import SessionLocal
from app.ingestion.chunking import split_text

def extract_pdf_pages(pdf_path: Path) -> list[tuple[int, str]]:
    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported")

    pages = []

    with pymupdf.open(str(pdf_path)) as pdf:
        for page_number, page in enumerate(pdf, start=1):
            content = page.get_text("text", sort=True).strip()

            if content:
                pages.append((page_number, content))

    if not pages:
        raise ValueError("No extractable text found. Scanned PDFs may require OCR.")

    return pages

def chunk_pdf_pages(pages: list[tuple[int, str]], chunk_size: int = 800, chunk_overlap: int = 120) -> list[tuple[int, str]]:
    chunks = []

    for page_number, content in pages:
        for chunk_content in split_text(content, chunk_size=chunk_size, chunk_overlap=chunk_overlap):
            chunks.append((page_number, chunk_content))

    return chunks

def ingest_pdf(pdf_path: Path, project_name: str) -> tuple[int, int, bool]:
    pages = extract_pdf_pages(pdf_path)
    chunks = chunk_pdf_pages(pages)

    with SessionLocal.begin() as db:
        project = db.scalar(select(Project).where(Project.name == project_name))

        if project is None:
            raise ValueError(f"Project not found: {project_name}")

        document = db.scalar(select(Document).where(Document.project_id == project.id, Document.file_name == pdf_path.name, Document.file_path == str(pdf_path)))

        if document is None:
            document = Document(project_id=project.id, file_name=pdf_path.name, document_type="unclassified", file_path=str(pdf_path))
            db.add(document)
            db.flush()

        existing_chunks = db.scalars(select(DocumentChunk).where(DocumentChunk.document_id == document.id).order_by(DocumentChunk.chunk_index)).all()

        unchanged = len(existing_chunks) == len(chunks) and all(old.page_number == page and old.content == content for old, (page, content) in zip(existing_chunks, chunks))

        if unchanged:
            return document.id, len(pages), False

        db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))

        for index, (page_number, content) in enumerate(chunks):
            chunk = DocumentChunk(document_id=document.id, chunk_index=index, content=content, page_number=page_number)
            db.add(chunk)

        return document.id, len(pages), True