from pathlib import Path

from app.ingestion.cost_record_csv import ingest_cost_records


def main():
    csv_path = Path("data/raw/cost_records_demo.csv")
    project_name = "Demo Ingestion Sandbox"

    inserted, updated = ingest_cost_records(csv_path, project_name)

    print(f"Inserted Cost Records: {inserted}")
    print(f"Updated Cost Records: {updated}")


if __name__ == "__main__":
    main()