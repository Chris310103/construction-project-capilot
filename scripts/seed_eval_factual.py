import json
from pathlib import Path

import pymupdf
from sqlalchemy import select

from app.db.models import Project
from app.db.session import SessionLocal
from app.ingestion.pdf import ingest_pdf


PROJECT_NAME = "Demo Evaluation Project"
FIXTURE_DIR = Path("eval/fixtures/factual")
CASE_FILE = Path("eval/answer_cases.json")


FACTS = [
    ("RFI", "EV-201", "Fire Damper Access", "Access hatch conflicts with corridor ceiling framing.", "Fire Protection Engineer"),
    ("RFI", "EV-202", "Stair Door Clearance", "Stair door reduces the required exit width.", "Architect"),
    ("Change Order", "EV-203", "Roof Insulation Upgrade", "Owner requests higher thermal resistance roof insulation.", "Cost Engineer"),
    ("Change Order", "EV-204", "Lobby Stone Substitution", "Original stone is unavailable and replacement requires approval.", "Architect"),
    ("Daily Report", "EV-205", "Concrete Delivery Interruption", "Level 6 concrete pour started late after truck delays.", "Site Superintendent"),
    ("Daily Report", "EV-206", "Basement Water Intrusion", "Rainwater entered the basement work zone.", "General Contractor"),
    ("Schedule Note", "EV-207", "Tower Crane Inspection", "Crane inspection postponed planned lifting operations.", "Scheduler"),
    ("Schedule Note", "EV-208", "Elevator Commissioning", "Commissioning awaits permanent electrical power.", "MEP Coordinator"),
    ("Cost Report", "EV-209", "Structural Steel Escalation", "Fabrication quotes increased above the baseline budget.", "Cost Manager"),
    ("Cost Report", "EV-210", "Curtain Wall Glazing Premium", "Special glazing raised forecast enclosure costs.", "Quantity Surveyor"),
    ("RFI", "EV-211", "Chilled Water Pipe Clash", "Pipe supports clash with cable trays above Level 3.", "Mechanical Engineer"),
    ("Daily Report", "EV-212", "Temporary Power Outage", "Power loss interrupted Level 4 lighting installation.", "Electrical Superintendent"),
    ("Change Order", "EV-213", "Fire Door Hardware Upgrade", "Owner requested upgraded stair door panic hardware.", "Project Manager"),
    ("Schedule Note", "EV-214", "Facade Sealant Curing", "Cold weather delayed sealant curing before inspection.", "Envelope Consultant"),
]


def create_pdf(path: Path, document_type: str, record_id: str, subject: str, description: str, owner: str):
    if path.exists():
        return

    content = "\n".join([
        f"Document Type: {document_type}",
        f"Record ID: {record_id}",
        f"Project: {PROJECT_NAME}",
        f"Subject: {subject}",
        f"Description: {description}",
        f"Responsible Party: {owner}",
    ])

    with pymupdf.open() as pdf:
        page = pdf.new_page()
        area = pymupdf.Rect(60, 60, 540, 750)
        page.insert_textbox(area, content, fontsize=11)
        pdf.save(str(path))


def main():
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

    with SessionLocal.begin() as db:
        project = db.scalar(select(Project).where(Project.name == PROJECT_NAME))

        if project is None:
            db.add(Project(name=PROJECT_NAME, description="Synthetic evaluation fixtures"))

    cases = json.loads(CASE_FILE.read_text(encoding="utf-8"))
    existing_ids = {case["id"] for case in cases}

    for index, (doc_type, record_id, subject, description, owner) in enumerate(FACTS, start=1):
        pdf_path = FIXTURE_DIR / f"{record_id}.pdf"
        create_pdf(pdf_path, doc_type, record_id, subject, description, owner)
        ingest_pdf(pdf_path, PROJECT_NAME)

        new_cases = [
            {
                "id": f"fact_{index:03d}_record",
                "category": "factual_retrieval",
                "project_name": PROJECT_NAME,
                "question": f"Which record documents the {subject.lower()} issue?",
                "must_contain": [record_id],
                "required_files": [pdf_path.name],
            },
            {
                "id": f"fact_{index:03d}_owner",
                "category": "factual_retrieval",
                "project_name": PROJECT_NAME,
                "question": f"Who is responsible for the {subject.lower()} issue?",
                "must_contain": [owner],
                "required_files": [pdf_path.name],
            },
        ]

        for case in new_cases:
            if case["id"] not in existing_ids:
                cases.append(case)
                existing_ids.add(case["id"])

    CASE_FILE.write_text(json.dumps(cases, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Evaluation cases: {len(cases)}")
    print(f"Generated documents: {len(FACTS)}")


if __name__ == "__main__":
    main()