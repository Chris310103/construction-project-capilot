from pathlib import Path

from app.ingestion.rfi_csv import ingest_rfis


def main():
    csv_path = Path("data/raw/rfis_demo.csv")

    inserted, updated = ingest_rfis(csv_path, "Demo Boston Office Tower")

    print(f"Inserted RFIs: {inserted}")
    print(f"Updated RFIs: {updated}")


if __name__ == "__main__":
    main()
