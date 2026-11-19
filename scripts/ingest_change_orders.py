from pathlib import Path

from sqlalchemy import select

from app.db.models import Project
from app.db.session import SessionLocal
from app.ingestion.change_order_csv import ingest_change_orders


PROJECT_NAME = "Demo Ingestion Sandbox"


def main():
    with SessionLocal.begin() as db:
        project = db.scalar(select(Project).where(Project.name == PROJECT_NAME))

        if project is None:
            db.add(Project(name=PROJECT_NAME, description="Isolated data ingestion demo"))

    csv_path = Path("data/raw/change_orders_demo.csv")
    inserted, updated = ingest_change_orders(csv_path, PROJECT_NAME)

    print(f"Inserted Change Orders: {inserted}")
    print(f"Updated Change Orders: {updated}")


if __name__ == "__main__":
    main()