import json
from pathlib import Path

import pymupdf
from sqlalchemy import select

from app.db.models import Project
from app.db.session import SessionLocal
from app.ingestion.pdf import ingest_pdf


PROJECT_NAME = "Demo Evaluation Project"
FIXTURE_DIR = Path("eval/fixtures/multidoc")
CASE_FILE = Path("eval/answer_cases.json")


ISSUES = [
    ("EV-301", "West stairwell", "Fire damper access blocked by framing",
     "Relocate access hatch", "Fire Protection Engineer", "damper", "hatch"),
    ("EV-302", "Level 6 corridor", "Sprinkler head clashes with light fixture",
     "Reroute sprinkler branch", "Plumbing Engineer", "sprinkler", "reroute"),
    ("EV-303", "East roof", "Exhaust fan clearance blocked by screen",
     "Resize roof screen", "Mechanical Engineer", "fan", "screen"),
    ("EV-304", "Basement ramp", "Waterproofing seam is leaking",
     "Replace membrane seam", "Waterproofing Contractor", "leaking", "membrane"),
    ("EV-305", "East lobby", "Stone floor tiles were cracked",
     "Replace damaged tiles", "Finishes Supervisor", "tiles", "replace"),
    ("EV-306", "Loading dock", "Forklift route blocked by fencing",
     "Shift temporary fence", "Site Superintendent", "forklift", "fence"),
    ("EV-307", "Level 3 slab", "Rebar cover is insufficient",
     "Install rebar spacers", "Structural Engineer", "rebar", "spacers"),
    ("EV-308", "Level 5 ceiling", "Cable tray conflicts with supply duct",
     "Reroute cable tray", "Electrical Engineer", "duct", "cable tray"),
    ("EV-309", "West facade", "Curtain wall anchor shows corrosion",
     "Replace anchor brackets", "Facade Engineer", "corrosion", "brackets"),
    ("EV-310", "North stair", "Door closer does not latch",
     "Adjust door closer", "Architect", "latch", "closer"),
    ("EV-311", "Level 2 plant room", "Chilled water pipe joint is leaking",
     "Reseal pipe joint", "Mechanical Contractor", "leaking", "reseal"),
    ("EV-312", "Mechanical room", "Air handling unit vibrates excessively",
     "Install vibration isolators", "MEP Engineer", "vibrates", "isolators"),
    ("EV-313", "South roof", "Standing water surrounds roof drain",
     "Regrade roof slope", "Roofing Contractor", "water", "regrade"),
    ("EV-314", "Tower crane zone", "High winds interrupted lifting",
     "Resequence crane lifts", "Construction Scheduler", "winds", "resequence"),
]


def create_pdf(path: Path, lines: list[str]) -> None:
    if path.exists():
        return

    with pymupdf.open() as pdf:
        page = pdf.new_page()
        area = pymupdf.Rect(60, 60, 540, 750)
        remaining = page.insert_textbox(area, "\n".join(lines), fontsize=11)

        if remaining < 0:
            raise ValueError(f"PDF text does not fit: {path.name}")

        pdf.save(str(path))


def main() -> None:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

    with SessionLocal.begin() as db:
        project = db.scalar(select(Project).where(Project.name == PROJECT_NAME))

        if project is None:
            db.add(Project(name=PROJECT_NAME, description="Synthetic evaluation documents"))

    cases = json.loads(CASE_FILE.read_text(encoding="utf-8"))
    existing_ids = {case["id"] for case in cases}
    created_cases = 0

    for code, location, observation, action, owner, observation_key, action_key in ISSUES:
        observation_pdf = FIXTURE_DIR / f"{code}-A.pdf"
        action_pdf = FIXTURE_DIR / f"{code}-B.pdf"

        create_pdf(observation_pdf, [
            "FIELD OBSERVATION", f"Project: {PROJECT_NAME}", f"Issue ID: {code}",
            f"Location: {location}", f"Observed condition: {observation}",
        ])

        create_pdf(action_pdf, [
            "CORRECTIVE ACTION MEMO", f"Project: {PROJECT_NAME}", f"Issue ID: {code}",
            f"Corrective action: {action}", f"Responsible party: {owner}",
        ])

        ingest_pdf(observation_pdf, PROJECT_NAME)
        ingest_pdf(action_pdf, PROJECT_NAME)

        source_files = [observation_pdf.name, action_pdf.name]

        new_cases = [
            {
                "id": f"md_{code[-3:]}_action",
                "category": "multi_document_reasoning",
                "project_name": PROJECT_NAME,
                "question": f"For issue {code}, what was observed and what corrective action was requested?",
                "must_contain": [observation_key, action_key],
                "required_files": source_files,
                "ground_truth": {"observation": observation, "action": action},
            },
            {
                "id": f"md_{code[-3:]}_owner",
                "category": "multi_document_reasoning",
                "project_name": PROJECT_NAME,
                "question": f"Who owns the corrective action for issue {code}, and what condition prompted it?",
                "must_contain": [owner, observation_key],
                "required_files": source_files,
                "ground_truth": {"observation": observation, "owner": owner},
            },
        ]

        if code == "EV-301":
            new_cases.append({
                "id": "md_301_location",
                "category": "multi_document_reasoning",
                "project_name": PROJECT_NAME,
                "question": "Where was issue EV-301 observed, and who owns the requested correction?",
                "must_contain": [location, owner],
                "required_files": source_files,
                "ground_truth": {"location": location, "owner": owner},
            })

        for case in new_cases:
            if case["id"] not in existing_ids:
                cases.append(case)
                existing_ids.add(case["id"])
                created_cases += 1

    CASE_FILE.write_text(json.dumps(cases, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Created evaluation PDFs: {len(ISSUES) * 2}")
    print(f"New evaluation cases: {created_cases}")
    print(f"Total evaluation cases: {len(cases)}")


if __name__ == "__main__":
    main()