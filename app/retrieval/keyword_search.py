from sqlalchemy import func, select

from app.db.models import Document, DocumentChunk, Project
from app.db.session import SessionLocal


def search_keyword_chunks(query: str, project_name: str, top_k: int = 3, document_type:str|None=None) -> list[dict]:
    query = query.strip()

    if not query:
        raise ValueError("Query cannot be empty")

    if not 1 <= top_k <= 20:
        raise ValueError("top_k must be between 1 and 20")

    with SessionLocal() as db:
        project_id = db.scalar(select(Project.id).where(Project.name == project_name))

        if project_id is None:
            raise ValueError(f"Project not found: {project_name}")

        text_vector = func.to_tsvector("english", DocumentChunk.content)
        search_query = func.websearch_to_tsquery("english", query)
        score = func.ts_rank_cd(text_vector, search_query)

        statement = select(
            DocumentChunk.id.label("chunk_id"), DocumentChunk.content, DocumentChunk.page_number,
            Document.file_name, Document.document_type, score.label("keyword_score")
        )
        statement = statement.join(Document, Document.id == DocumentChunk.document_id)
        statement = statement.where(Document.project_id == project_id, text_vector.bool_op("@@")(search_query))

        if document_type is not None:
            statement = statement.where(Document.document_type == document_type)

        statement = statement.order_by(score.desc(), DocumentChunk.id).limit(top_k)

        rows = db.execute(statement).all()

    return [
        {
            "chunk_id": row.chunk_id,
            "content": row.content,
            "page_number": row.page_number,
            "file_name": row.file_name,
            "document_type": row.document_type,
            "keyword_score": float(row.keyword_score),
        }
        for row in rows
    ]