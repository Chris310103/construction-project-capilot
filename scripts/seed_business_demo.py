from datetime import date
from decimal import Decimal

from sqlalchemy import func, select

from app.db.models import ChangeOrder, CostRecord, DailyReport, Document, Project, RFI, ScheduleActivity
from app.db.session import SessionLocal


def main():
    with SessionLocal() as db:
        project = db.scalar(select(Project).where(Project.name == "Demo Boston Office Tower"))

        if project is None:
            raise RuntimeError("Please run python -m scripts.seed_demo first.")

        project_id = project.id
        source = db.scalar(select(Document).where(Document.project_id == project_id, Document.file_name == "RFI_037.pdf"))

        if source is None:
            raise RuntimeError("Demo RFI document not found. Run python -m scripts.seed_demo first.")

        rfi = db.scalar(select(RFI).where(RFI.project_id == project_id, RFI.rfi_number == "RFI-037"))

        if rfi is None:
            rfi = RFI(project_id=project_id, source_document_id=source.id, rfi_number="RFI-037", subject="HVAC Structural Conflict", question="HVAC duct conflicts with structural beam B17.", status="open", responsible_party="Mechanical Engineer", submitted_date=date(2026, 7, 12), due_date=date(2026, 7, 20), schedule_impact_days=5)
            db.add(rfi)

        change_order = db.scalar(select(ChangeOrder).where(ChangeOrder.project_id == project_id, ChangeOrder.change_order_number == "CO-014"))

        if change_order is None:
            change_order = ChangeOrder(project_id=project_id, change_order_number="CO-014", title="Additional HVAC Equipment", description="Additional HVAC installation work", status="approved", amount=Decimal("120000.00"), schedule_impact_days=4, submitted_date=date(2026, 7, 10), approved_date=date(2026, 7, 18))
            db.add(change_order)

        report_date = date(2026, 7, 15)
        report = db.scalar(select(DailyReport).where(DailyReport.project_id == project_id, DailyReport.report_date == report_date, DailyReport.work_completed == "Concrete slab Level 3"))

        if report is None:
            report = DailyReport(project_id=project_id, report_date=report_date, weather="Rain", workers_on_site=42, work_completed="Concrete slab Level 3", issues="Concrete delivery delayed by 2 hours.", safety_incidents=0)
            db.add(report)

        activities = [
            {"activity_code": "MEP-100", "name": "MEP Rough-In", "planned_start": date(2026, 8, 15), "planned_finish": date(2026, 10, 20), "actual_start": date(2026, 9, 1), "forecast_finish": date(2026, 10, 25), "percent_complete": Decimal("45.00"), "total_float_days": 0, "is_critical": True, "status": "in_progress"},
            {"activity_code": "STR-200", "name": "Level 3 Structure", "planned_start": date(2026, 7, 1), "planned_finish": date(2026, 7, 20), "actual_start": date(2026, 7, 2), "actual_finish": date(2026, 7, 22), "percent_complete": Decimal("100.00"), "total_float_days": 3, "is_critical": False, "status": "completed"},
        ]

        for fields in activities:
            existing = db.scalar(select(ScheduleActivity).where(ScheduleActivity.project_id == project_id, ScheduleActivity.activity_code == fields["activity_code"]))

            if existing is None:
                db.add(ScheduleActivity(project_id=project_id, **fields))

        snapshot_date = date(2026, 8, 1)
        costs = [
            ("03-100", "Concrete", "500000.00", "520000.00", "550000.00"),
            ("23-100", "HVAC", "800000.00", "650000.00", "850000.00"),
            ("26-100", "Electrical", "400000.00", "380000.00", "420000.00"),
        ]

        for code, category, budget, actual, forecast in costs:
            existing = db.scalar(select(CostRecord).where(CostRecord.project_id == project_id, CostRecord.cost_code == code, CostRecord.as_of_date == snapshot_date))

            if existing is None:
                record = CostRecord(project_id=project_id, cost_code=code, category=category, budget_amount=Decimal(budget), actual_amount=Decimal(actual), forecast_amount=Decimal(forecast), currency="USD", as_of_date=snapshot_date)
                db.add(record)

        db.commit()

    with SessionLocal() as db:
        open_rfis = db.scalar(select(func.count(RFI.id)).where(RFI.project_id == project_id, RFI.status == "open"))
        approved_total = db.scalar(select(func.coalesce(func.sum(ChangeOrder.amount), 0)).where(ChangeOrder.project_id == project_id, ChangeOrder.status == "approved"))
        critical_activities = db.scalars(select(ScheduleActivity).where(ScheduleActivity.project_id == project_id, ScheduleActivity.is_critical.is_(True))).all()
        cost_records = db.scalars(select(CostRecord).where(CostRecord.project_id == project_id, CostRecord.as_of_date == snapshot_date)).all()

        print(f"Project ID: {project_id}")
        print(f"Open RFIs: {open_rfis}")
        print(f"Approved Change Orders: ${approved_total}")
        print(f"Critical Activities: {[item.activity_code for item in critical_activities]}")

        for record in cost_records:
            if record.budget_amount is not None and record.forecast_amount is not None:
                variance = record.forecast_amount - record.budget_amount
                print(f"{record.category} forecast variance: ${variance}")


if __name__ == "__main__":
    main()