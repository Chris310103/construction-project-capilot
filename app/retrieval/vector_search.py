from openai import OpenAI
from sqlalchemy import select

from app.core.config import settings
from app.db.models import Document, DocumentChunk, Project
from app.db.session import SessionLocal


EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


def search_similar_chunks(question: str, project_name: str, top_k: int = 3) -> list[dict]:
    question = question.strip()

    if not question:
        raise ValueError("Question cannot be empty")

    if not 1 <= top_k <= 20:
        raise ValueError("top_k must be between 1 and 20")

    with SessionLocal() as db:
        project = db.scalar(select(Project).where(Project.name == project_name))

        if project is None:
            raise ValueError(f"Project not found: {project_name}")

        project_id = project.id
        existing_id = db.scalar(select(DocumentChunk.id).join(Document, Document.id == DocumentChunk.document_id).where(Document.project_id == project_id, DocumentChunk.embedding.is_not(None)).limit(1))

    if existing_id is None:
        return []

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is missing")

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=question, encoding_format="float")
    query_vector = response.data[0].embedding

    if len(query_vector) != EMBEDDING_DIMENSIONS:
        raise ValueError("Query embedding dimension mismatch")

    distance = DocumentChunk.embedding.cosine_distance(query_vector)

    statement = select(DocumentChunk.id.label("chunk_id"), DocumentChunk.content, DocumentChunk.page_number, Document.file_name, Document.document_type, distance.label("distance")).join(Document, Document.id == DocumentChunk.document_id).where(Document.project_id == project_id, DocumentChunk.embedding.is_not(None)).order_by(distance).limit(top_k)

    with SessionLocal() as db:
        rows = db.execute(statement).all()

    results = []

    for row in rows:
        results.append({
            "chunk_id": row.chunk_id,
            "file_name": row.file_name,
            "document_type": row.document_type,
            "page_number": row.page_number,
            "content": row.content,
            "similarity": 1.0 - float(row.distance),
        })

    return results