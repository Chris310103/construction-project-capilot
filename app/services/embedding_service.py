import logging

from openai import OpenAI
from sqlalchemy import select

from app.core.config import settings
from app.db.models import Document, DocumentChunk
from app.db.session import SessionLocal


logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536


def embed_document_chunks(document_id: int, batch_size: int = 32) -> int:
    if batch_size < 1:
        raise ValueError("batch_size must be positive")

    with SessionLocal() as db:
        if db.get(Document, document_id) is None:
            raise ValueError(f"Document not found: {document_id}")

        statement = select(DocumentChunk.id, DocumentChunk.content)
        statement = statement.where(DocumentChunk.document_id == document_id)
        statement = statement.where(DocumentChunk.embedding.is_(None))
        statement = statement.order_by(DocumentChunk.id)

        pending = db.execute(statement).all()

    if not pending:
        return 0

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is missing")

    client = OpenAI(api_key=settings.openai_api_key)
    total_stored = 0

    for start in range(0, len(pending), batch_size):
        batch = pending[start:start + batch_size]
        texts = [content for chunk_id, content in batch]

        if any(not content.strip() for content in texts):
            raise ValueError("Empty chunk content cannot be embedded")

        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts,
            encoding_format="float",
        )

        vectors = {item.index: item.embedding for item in response.data}

        if set(vectors) != set(range(len(batch))):
            raise RuntimeError("Embedding response indices do not match inputs")

        with SessionLocal.begin() as db:
            for index, (chunk_id, original_content) in enumerate(batch):
                vector = vectors[index]

                if len(vector) != EMBEDDING_DIMENSIONS:
                    raise ValueError(f"Unexpected embedding dimensions: {len(vector)}")

                chunk = db.get(DocumentChunk, chunk_id)

                if chunk is not None and chunk.content == original_content and chunk.embedding is None:
                    chunk.embedding = vector
                    total_stored += 1

    return total_stored


def index_document_safely(document_id: int) -> None:
    try:
        count = embed_document_chunks(document_id)
        logger.info("Indexed document %s: %s embeddings stored", document_id, count)
    except Exception:
        logger.exception("Embedding failed for document %s", document_id)