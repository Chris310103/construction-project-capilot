from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models import Project, Document, DocumentChunk
from app.db.session import SessionLocal


def main():
    with SessionLocal() as db:
        project = db.scalar(select(Project).where(Project.name == "Demo Boston Office Tower"))

        if project is None:
            project = Project(name="Demo Boston Office Tower", description="Demo construction project")
            db.add(project)
            db.flush()

        document = db.scalar(select(Document).where(Document.project_id == project.id, Document.file_name == "RFI_037.pdf"))

        if document is None:
            document = Document(project=project, file_name="RFI_037.pdf", document_type="RFI", file_path="data/raw/RFI_037.pdf")
            db.add(document)
            db.flush()

        demo_chunks = [
            ("HVAC duct conflicts with structural beam B17.", 1),
            ("The contractor requested revised HVAC routing.", 2),
        ]

        for index, (content, page) in enumerate(demo_chunks):
            existing = db.scalar(select(DocumentChunk).where(DocumentChunk.document_id == document.id, DocumentChunk.chunk_index == index))

            if existing is None:
                chunk = DocumentChunk(document=document, chunk_index=index, content=content, page_number=page)
                db.add(chunk)

        db.commit()

    with SessionLocal() as db:
        query = select(Project).options(selectinload(Project.documents).selectinload(Document.chunks)).where(Project.name == "Demo Boston Office Tower")
        project = db.scalar(query)

        print(f"Project: {project.name}")

        for document in project.documents:
            print(f"Document: {document.file_name}")

            for chunk in sorted(document.chunks, key=lambda item: item.chunk_index):
                print(f"Chunk {chunk.chunk_index}: {chunk.content}")
                print(f"Page: {chunk.page_number}")
                print(f"Embedding: {chunk.embedding}")


if __name__ == "__main__":
    main()