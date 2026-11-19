import re

from sqlalchemy import or_, select

from app.db.models import Document, DocumentChunk, Project
from app.db.session import SessionLocal


IDENTIFIER_PATTERN = re.compile(r"\b[A-Z]{2,10}-\d{2,5}(?:-[A-Z0-9]+)*\b", re.I)


def extract_identifiers(question: str) -> list[str]:
    identifiers = [value.upper() for value in IDENTIFIER_PATTERN.findall(question)]
    return list(dict.fromkeys(identifiers))


def search_identifier_chunks(question: str, project_name: str, top_k: int = 20, document_type: str | None = None) -> list[dict]:
    identifiers = extract_identifiers(question)

    if not identifiers:
        return []

    with SessionLocal() as db:
        project_id = db.scalar(select(Project.id).where(Project.name == project_name))

        if project_id is None:
            raise ValueError(f"Project not found: {project_name}")

        statement = select(
            DocumentChunk.id.label("chunk_id"),
            DocumentChunk.content,
            DocumentChunk.page_number,
            Document.file_name,
            Document.document_type,
        )
        statement = statement.join(Document, Document.id == DocumentChunk.document_id)
        statement = statement.where(Document.project_id == project_id)
        statement = statement.where(or_(*[DocumentChunk.content.ilike(f"%{code}%") for code in identifiers]))

        if document_type is not None:
            statement = statement.where(Document.document_type == document_type)

        rows = db.execute(statement.order_by(DocumentChunk.id)).all()

    results = []

    for row in rows:
        matched = any(
            re.search(
                rf"(?im)^[ \t]*(?:Issue ID|Record ID|RFI Number|Change Order Number|Activity Code):[ \t]*{re.escape(code)}[ \t]*$",
                row.content,
            )
            for code in identifiers
        )

        if not matched:
            continue

        results.append({
            "chunk_id": row.chunk_id,
            "content": row.content,
            "page_number": row.page_number,
            "file_name": row.file_name,
            "document_type": row.document_type,
            "rrf_score": 0.0,
            "vector_rank": None,
            "keyword_rank": None,
            "similarity": None,
            "keyword_score": None,
            "match_type": "exact_identifier",
        })

    return results[:top_k]