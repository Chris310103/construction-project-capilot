import json
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from app.db.models import CostRecord, Project, RFI, RFIActivityLink, ScheduleActivity
from app.db.session import SessionLocal


CASE_FILE = Path("eval/answer_cases.json")
SNAPSHOT_DATE = date(2026, 9, 1)

SCENARIOS = [
    ("Airport Terminal", "HVAC", "Concrete", "MEP Coordination", 4),
    ("Medical Center", "Electrical", "Concrete", "Emergency Power Installation", 6),
    ("Transit Hub", "Structural Steel", "Finishes", "Platform Steel Erection", 3),
    ("Campus Laboratory", "HVAC", "Electrical", "Ventilation Commissioning", 8),
    ("Waterfront Tower", "Facade", "Concrete", "Curtain Wall Installation", 5),
    ("Logistics Warehouse", "Electrical", "Fire Protection", "Fire Alarm Integration", 7),
    ("Civic Library", "Roofing", "Finishes", "Roof Membrane Installation", 2),
    ("Sports Arena", "Structural Steel", "Mechanical", "Roof Truss Installation", 9),
    ("Data Center", "Mechanical", "Electrical", "Cooling System Commissioning", 5),
]


def upsert(db, model, keys: dict, values: dict):
    record = db.scalar(select(model).filter_by(**keys))

    if record is None:
        record = model(**keys, **values)
        db.add(record)
    else:
        for field, value in values.items():
            setattr(record, field, value)

    db.flush()
    return record


def seed_scenario(db, index: int, scenario: tuple) -> list[dict]:
    label, high_category, low_category, activity_name, delay_days = scenario
    project_name = f"Eval Risk {label}"
    prefix = f"ER-{index:02d}"

    project = upsert(db, Project, {"name": project_name}, {
        "description": "Synthetic schedule and cost evaluation project"
    })

    high_variance = Decimal(9000 + index * 3000)
    low_variance = Decimal(2000 + index * 500)

    costs = [
        ("01-100", high_category, Decimal(230000 + index * 10000), high_variance),
        ("02-100", low_category, Decimal(110000 + index * 5000), low_variance),
    ]

    for cost_code, category, budget, variance in costs:
        upsert(db, CostRecord, {
            "project_id": project.id,
            "cost_code": cost_code,
            "as_of_date": SNAPSHOT_DATE,
        }, {
            "category": category,
            "budget_amount": budget,
            "forecast_amount": budget + variance,
            "currency": "USD",
        })

    critical_code = f"{prefix}-CRIT"
    planned_finish = date(2026, 9, 15)
    forecast_finish = planned_finish + timedelta(days=delay_days)

    activity = upsert(db, ScheduleActivity, {
        "project_id": project.id,
        "activity_code": critical_code,
    }, {
        "name": activity_name,
        "planned_start": date(2026, 8, 1),
        "planned_finish": planned_finish,
        "actual_start": date(2026, 8, 2),
        "forecast_finish": forecast_finish,
        "actual_finish": None,
        "percent_complete": Decimal("55.00"),
        "total_float_days": 0,
        "is_critical": True,
        "status": "in_progress",
    })

    rfi_number = f"{prefix}-RFI"

    rfi = upsert(db, RFI, {
        "project_id": project.id,
        "rfi_number": rfi_number,
    }, {
        "subject": f"Clarification for {activity_name}",
        "question": f"Please clarify coordination requirements for {activity_name}.",
        "status": "open",
        "schedule_impact_days": None,
    })

    upsert(db, RFIActivityLink, {
        "rfi_id": rfi.id,
        "activity_id": activity.id,
    }, {
        "link_source": "evaluation_fixture",
        "note": "Synthetic unverified association; causation is not established.",
        "is_verified": False,
    })

    return [
        {
            "id": f"risk_{index:02d}_cost",
            "category": "schedule_cost_analysis",
            "project_name": project_name,
            "question": f"In {project_name}, which cost category has the largest forecast overrun and by how much?",
            "must_contain": [high_category, f"{high_variance:,}"],
            "required_tables": ["cost_records"],
            "ground_truth": {
                "category": high_category,
                "variance": str(high_variance),
                "as_of_date": SNAPSHOT_DATE.isoformat(),
            },
        },
        {
            "id": f"risk_{index:02d}_schedule",
            "category": "schedule_cost_analysis",
            "project_name": project_name,
            "question": f"For {project_name}, which critical activity has a forecast delay and how many calendar days?",
            "must_contain": [critical_code, str(delay_days)],
            "required_tables": ["schedule_activities"],
            "ground_truth": {
                "activity_code": critical_code,
                "forecast_variance_days": delay_days,
                "risk_level": "high",
            },
        },
        {
            "id": f"risk_{index:02d}_link",
            "category": "schedule_cost_analysis",
            "project_name": project_name,
            "question": (
                f"For {project_name}, which open RFI is linked to the critical activity, "
                f"is the link verified, and what is the activity's forecast finish variance?"
            ),
            "must_contain": [rfi_number, critical_code, str(delay_days)],
            "required_tables": ["rfi_activity_links", "schedule_activities"],
            "ground_truth": {
                "rfi_number": rfi_number,
                "activity_code": critical_code,
                "is_verified": False,
                "forecast_variance_days": delay_days,
                "causation_established": False,
            },
        },
    ]


def main():
    cases = json.loads(CASE_FILE.read_text(encoding="utf-8"))
    existing_ids = {case["id"] for case in cases}
    added = 0

    with SessionLocal.begin() as db:
        for index, scenario in enumerate(SCENARIOS, start=1):
            new_cases = seed_scenario(db, index, scenario)

            for case in new_cases:
                if case["id"] not in existing_ids:
                    cases.append(case)
                    existing_ids.add(case["id"])
                    added += 1

    CASE_FILE.write_text(json.dumps(cases, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Evaluation projects: {len(SCENARIOS)}")
    print(f"New evaluation cases: {added}")
    print(f"Total evaluation cases: {len(cases)}")


if __name__ == "__main__":
    main()