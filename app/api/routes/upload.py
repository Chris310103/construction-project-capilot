import re
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, BackgroundTasks
from sqlalchemy import func, select

from app.db.models import Document, DocumentChunk, Project
from app.db.session import SessionLocal
from app.ingestion.router import classify_document, ingest_document, validate_document
from app.services.embedding_service import index_document_safely

router = APIRouter(tags=["Documents"])
UPLOAD_ROOT = Path("data/uploads")
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


@router.post("/projects/{project_id}/documents/upload")
def upload_document(project_id: int, background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    with SessionLocal() as db:
        project = db.get(Project, project_id)

        if project is None:
            raise HTTPException(status_code=404, detail="Project not found")

        project_name = project.name

    filename = file.filename or ""

    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 _().-]{0,120}\.(csv|pdf)", filename, re.I):
        raise HTTPException(status_code=400, detail="Invalid filename or unsupported extension")

    content = file.file.read(MAX_UPLOAD_BYTES + 1)

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 10 MB limit")

    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    upload_dir = UPLOAD_ROOT / str(project_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    target = upload_dir / filename
    staging = upload_dir / f"pending_{uuid4().hex}_{filename}"
    backup = upload_dir / f"backup_{uuid4().hex}_{filename}"

    staging.write_bytes(content)
    replaced = False

    try:
        document_type = classify_document(staging)
        validate_document(staging, document_type)

        if target.exists():
            target.replace(backup)

        staging.replace(target)
        replaced = True

        ingestion_result = ingest_document(target, project_name, document_type)

    except Exception as exc:
        if replaced:
            target.unlink(missing_ok=True)

        if backup.exists():
            backup.replace(target)

        if isinstance(exc, ValueError):
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        raise

    finally:
        staging.unlink(missing_ok=True)
        backup.unlink(missing_ok=True)

    with SessionLocal() as db:
        document = db.scalar(select(Document).where(Document.project_id == project_id, Document.file_name == filename))

        pending = db.scalar(
            select(func.count(DocumentChunk.id)).where(
                DocumentChunk.document_id == document.id,
                DocumentChunk.embedding.is_(None)
            )
        )

    if pending > 0:
        background_tasks.add_task(index_document_safely, document.id)

    return {
        "project_id": project_id,
        "document_id": document.id,
        "filename": filename,
        "document_type": document_type,
        "ingestion": ingestion_result,
        "index_status": "pending_embedding" if pending else "ready",
    }

@router.get("/projects/{project_id}/documents/{document_id}/index-status")
def get_document_index_status(project_id: int, document_id: int):
    with SessionLocal() as db:
        document = db.get(Document, document_id)

        if document is None or document.project_id != project_id:
            raise HTTPException(status_code=404, detail="Document not found")

        statement = select(
            func.count(DocumentChunk.id),
            func.count(DocumentChunk.embedding),
        ).where(DocumentChunk.document_id == document_id)

        total_chunks, embedded_chunks = db.execute(statement).one()

    if total_chunks == 0:
        status = "no_chunks"
    elif embedded_chunks == total_chunks:
        status = "ready"
    else:
        status = "pending_embedding"

    return {
        "project_id": project_id,
        "document_id": document_id,
        "index_status": status,
        "total_chunks": total_chunks,
        "embedded_chunks": embedded_chunks,
        "pending_chunks": total_chunks - embedded_chunks,
    }