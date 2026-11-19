import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from app.db.models import ChangeOrder, CostRecord, Project, RFI
from app.db.session import SessionLocal


CASE_FILE = Path("eval/answer_cases.json")

SCENARIOS = [
    ("Alpha", "EA"),
    ("Bravo", "EB"),
    ("Charlie", "EC"),
    ("Delta", "ED"),
    ("Echo", "EE"),
    ("Foxtrot", "EF"),
    ("Golf", "EG"),
]


def seed_project(db, name: str, code: str, index: int) -> dict:
    project = db.scalar(select(Project).where(Project.name == name))

    if project is None:
        project = Project(name=name, description="Synthetic SQL evaluation project")
        db.add(project)
        db.flush()

    approved_a = Decimal(10000 + 3000 * index)
    approved_b = Decimal(7000 + 1000 * index)

    change_orders = [
        (f"{code}-CO-01", "Approved ventilation change", "approved", approved_a),
        (f"{code}-CO-02", "Approved electrical change", "approved", approved_b),
        (f"{code}-CO-03", "Pending facade change", "pending", Decimal("900000")),
    ]

    for number, title, status, amount in change_orders:
        query = select(ChangeOrder.id).where(ChangeOrder.project_id == project.id)
        query = query.where(ChangeOrder.change_order_number == number)

        if db.scalar(query) is None:
            db.add(ChangeOrder(
                project_id=project.id, change_order_number=number,
                title=title, status=status, amount=amount
            ))

    open_numbers = [f"{code}-RFI-01", f"{code}-RFI-02"]
    rfi_rows = [
        (open_numbers[0], "Mechanical clearance", "open"),
        (open_numbers[1], "Electrical coordination", "open"),
        (f"{code}-RFI-03", "Completed foundation clarification", "closed"),
    ]

    for number, subject, status in rfi_rows:
        query = select(RFI.id).where(RFI.project_id == project.id, RFI.rfi_number == number)

        if db.scalar(query) is None:
            db.add(RFI(
                project_id=project.id, rfi_number=number, subject=subject,
                question=f"Please clarify {subject.lower()}.", status=status
            ))

    concrete_budget = Decimal(100000 + 5000 * index)
    hvac_budget = Decimal(200000 + 7000 * index)
    concrete_variance = Decimal(6000 + 1000 * index)
    hvac_variance = Decimal(17000 + 2000 * index)

    snapshots = [
        ("03-100", "Concrete", date(2026, 9, 1), concrete_budget, concrete_budget + concrete_variance),
        ("23-100", "HVAC", date(2026, 9, 1), hvac_budget, hvac_budget + hvac_variance),
        ("23-100", "HVAC", date(2026, 8, 1), hvac_budget, hvac_budget + Decimal("80000")),
    ]

    for cost_code, category, as_of_date, budget, forecast in snapshots:
        query = select(CostRecord.id).where(CostRecord.project_id == project.id)
        query = query.where(CostRecord.cost_code == cost_code, CostRecord.as_of_date == as_of_date)

        if db.scalar(query) is None:
            db.add(CostRecord(
                project_id=project.id, cost_code=cost_code, category=category,
                as_of_date=as_of_date, budget_amount=budget,
                forecast_amount=forecast, currency="USD"
            ))

    return {
        "approved_total": approved_a + approved_b,
        "open_numbers": open_numbers,
        "hvac_variance": hvac_variance,
        "total_variance": concrete_variance + hvac_variance,
    }


def build_cases(name: str, code: str, facts: dict) -> list[dict]:
    return [
        {
            "id": f"sql_{code}_approved",
            "category": "sql_aggregation",
            "project_name": name,
            "question": f"For {name}, what is the total amount of approved change orders?",
            "must_contain": [f"{facts['approved_total']:,}"],
            "required_tables": ["change_orders"],
            "ground_truth": {"approved_total": str(facts["approved_total"])},
        },
        {
            "id": f"sql_{code}_open",
            "category": "sql_aggregation",
            "project_name": name,
            "question": f"For {name}, how many RFIs are open and what are their identifiers?",
            "must_contain": facts["open_numbers"],
            "required_tables": ["rfis"],
            "ground_truth": {"open_count": 2, "open_rfis": facts["open_numbers"]},
        },
        {
            "id": f"sql_{code}_largest",
            "category": "sql_aggregation",
            "project_name": name,
            "question": f"For {name}, which cost category has the largest positive forecast variance?",
            "must_contain": ["HVAC", f"{facts['hvac_variance']:,}"],
            "required_tables": ["cost_records"],
            "ground_truth": {"category": "HVAC", "variance": str(facts["hvac_variance"])},
        },
        {
            "id": f"sql_{code}_variance",
            "category": "sql_aggregation",
            "project_name": name,
            "question": f"For {name}, what is the total forecast cost variance in the latest cost snapshot?",
            "must_contain": [f"{facts['total_variance']:,}"],
            "required_tables": ["cost_records"],
            "ground_truth": {"total_variance": str(facts["total_variance"])},
        },
    ]


def main():
    cases = json.loads(CASE_FILE.read_text(encoding="utf-8"))
    existing_ids = {case["id"] for case in cases}
    added = 0

    with SessionLocal.begin() as db:
        for index, (label, code) in enumerate(SCENARIOS):
            name = f"Eval SQL {label}"
            facts = seed_project(db, name, code, index)

            for case in build_cases(name, code, facts):
                if case["id"] not in existing_ids:
                    cases.append(case)
                    existing_ids.add(case["id"])
                    added += 1

    CASE_FILE.write_text(json.dumps(cases, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"SQL evaluation projects: {len(SCENARIOS)}")
    print(f"New evaluation cases: {added}")
    print(f"Total evaluation cases: {len(cases)}")


if __name__ == "__main__":
    main()