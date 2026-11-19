from pathlib import Path

from app.ingestion.daily_report_csv import ingest_daily_reports


def main():
    csv_path = Path("data/raw/daily_reports_demo.csv")
    project_name = "Demo Ingestion Sandbox"

    inserted, updated = ingest_daily_reports(csv_path, project_name)

    print(f"Inserted Daily Reports: {inserted}")
    print(f"Updated Daily Reports: {updated}")


if __name__ == "__main__":
    main()