from openai import OpenAI
from sqlalchemy import select

from app.core.config import settings
from app.db.models import DocumentChunk
from app.db.session import SessionLocal


EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
BATCH_SIZE = 32


def main():
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is missing in .env")

    client = OpenAI(api_key=settings.openai_api_key)

    with SessionLocal() as db:
        pending = db.execute(select(DocumentChunk.id, DocumentChunk.content).where(DocumentChunk.embedding.is_(None)).order_by(DocumentChunk.id)).all()

    print(f"Chunks without embeddings: {len(pending)}")

    total_stored = 0

    for start in range(0, len(pending), BATCH_SIZE):
        batch = pending[start:start + BATCH_SIZE]
        texts = [content for chunk_id, content in batch]

        if any(not content.strip() for content in texts):
            raise ValueError("Empty chunk content cannot be embedded")

        response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts, encoding_format="float")

        if len(response.data) != len(batch):
            raise RuntimeError("Embedding response count does not match input count")

        vectors = {item.index: item.embedding for item in response.data}

        with SessionLocal.begin() as db:
            for index, (chunk_id, content) in enumerate(batch):
                vector = vectors[index]

                if len(vector) != EMBEDDING_DIMENSIONS:
                    raise ValueError(f"Invalid embedding dimensions: {len(vector)}")

                chunk = db.get(DocumentChunk, chunk_id)

                if chunk is not None and chunk.content == content and chunk.embedding is None:
                    chunk.embedding = vector
                    total_stored += 1

        print(f"Processed batch: {min(start + BATCH_SIZE, len(pending))}/{len(pending)}")

    print(f"Embeddings stored: {total_stored}")


if __name__ == "__main__":
    main()