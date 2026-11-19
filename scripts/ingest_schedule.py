from pathlib import Path

from app.ingestion.schedule_csv import ingest_schedule


def main():
    csv_path = Path("data/raw/schedule_demo.csv")
    project_name = "Demo Ingestion Sandbox"

    inserted, updated = ingest_schedule(csv_path, project_name)

    print(f"Inserted Schedule Activities: {inserted}")
    print(f"Updated Schedule Activities: {updated}")


if __name__ == "__main__":
    main()