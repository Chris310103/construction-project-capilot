from sqlalchemy import func, select

from app.db.models import ChangeOrder, Project, RFI, ScheduleActivity, RFIActivityLink
from app.db.session import SessionLocal
from decimal import Decimal
from app.db.models import CostRecord


def get_total_approved_change_orders(project_name: str) -> dict:
    with SessionLocal() as db:
        project = db.scalar(
            select(Project).where(Project.name == project_name)
        )

        if project is None:
            raise ValueError(f"Project not found: {project_name}")

        total = db.scalar(
            select(func.coalesce(func.sum(ChangeOrder.amount), 0))
            .where(
                ChangeOrder.project_id == project.id,
                ChangeOrder.status == "approved",
            )
        )

        return {
            "project_name": project.name,
            "approved_change_order_total": float(total),
            "currency": "USD",
        }


def get_open_rfis(project_name: str) -> dict:
    with SessionLocal() as db:
        project = db.scalar(select(Project).where(Project.name == project_name))

        if project is None:
            raise ValueError(f"Project not found: {project_name}")

        rfis = db.scalars(select(RFI).where(RFI.project_id == project.id, RFI.status == "open").order_by(RFI.rfi_number)).all()

        results = []

        for rfi in rfis:
            results.append({
                "rfi_number": rfi.rfi_number,
                "subject": rfi.subject,
                "status": rfi.status,
                "schedule_impact_days": rfi.schedule_impact_days
            })

        return {
            "project_name": project.name,
            "open_rfi_count": len(results),
            "rfis": results
        }


def get_cost_variances(project_name: str) -> dict:
    with SessionLocal() as db:
        project = db.scalar(select(Project).where(Project.name == project_name))

        if project is None:
            raise ValueError(f"Project not found: {project_name}")

        latest_date = db.scalar(select(func.max(CostRecord.as_of_date)).where(CostRecord.project_id == project.id))

        if latest_date is None:
            return {"project_name": project.name, "as_of_date": None, "message": "No cost records available.", "items": []}

        records = db.scalars(select(CostRecord).where(CostRecord.project_id == project.id, CostRecord.as_of_date == latest_date).order_by(CostRecord.cost_code)).all()

        currencies = {record.currency for record in records}

        if len(currencies) != 1:
            raise ValueError("Multiple currencies require separate cost analysis")

        total_budget = Decimal("0.00")
        total_forecast = Decimal("0.00")
        items = []
        missing_cost_codes = []

        for record in records:
            if record.budget_amount is None or record.forecast_amount is None:
                missing_cost_codes.append(record.cost_code)
                continue

            variance = record.forecast_amount - record.budget_amount
            total_budget += record.budget_amount
            total_forecast += record.forecast_amount

            items.append({
                "cost_code": record.cost_code,
                "category": record.category,
                "budget": str(record.budget_amount),
                "forecast": str(record.forecast_amount),
                "variance": str(variance),
                "over_budget": variance > 0
            })

        return {
            "project_name": project.name,
            "as_of_date": latest_date.isoformat(),
            "currency": records[0].currency,
            "total_budget": str(total_budget) if items else None,
            "total_forecast": str(total_forecast) if items else None,
            "total_variance": str(total_forecast - total_budget) if items else None,
            "items": items,
            "missing_cost_codes": missing_cost_codes
        }

def analyze_schedule_risks(project_name: str) -> dict:
    with SessionLocal() as db:
        project = db.scalar(select(Project).where(Project.name == project_name))

        if project is None:
            raise ValueError(f"Project not found: {project_name}")

        activities = db.scalars(select(ScheduleActivity).where(ScheduleActivity.project_id == project.id).order_by(ScheduleActivity.activity_code)).all()

        results = []

        for activity in activities:
            if activity.actual_finish is not None:
                finish_date = activity.actual_finish
                finish_type = "actual"
            elif activity.forecast_finish is not None:
                finish_date = activity.forecast_finish
                finish_type = "forecast"
            else:
                finish_date = None
                finish_type = None

            variance_days = (finish_date - activity.planned_finish).days if finish_date else None

            if activity.actual_finish is not None:
                risk_level = "completed"
            elif variance_days is None:
                risk_level = "unknown"
            elif variance_days > 0 and activity.is_critical is True:
                risk_level = "high"
            elif variance_days > 0:
                risk_level = "medium"
            elif activity.is_critical is True:
                risk_level = "watch"
            else:
                risk_level = "low"

            results.append({
                "activity_code": activity.activity_code,
                "name": activity.name,
                "status": activity.status,
                "is_critical": activity.is_critical,
                "total_float_days": activity.total_float_days,
                "planned_finish": activity.planned_finish.isoformat(),
                "finish_date": finish_date.isoformat() if finish_date else None,
                "finish_type": finish_type,
                "finish_variance_days": variance_days,
                "risk_level": risk_level
            })

        return {
            "project_name": project.name,
            "critical_activity_count": sum(item["is_critical"] is True for item in results),
            "activities": results,
            "note": "Finish variances use calendar days. Risk levels are preliminary indicators, not CPM calculations."
        }

def get_rfi_schedule_links(project_name: str) -> dict:
    with SessionLocal() as db:
        project = db.scalar(select(Project).where(Project.name == project_name))

        if project is None:
            raise ValueError(f"Project not found: {project_name}")

        query = select(RFIActivityLink, RFI, ScheduleActivity)
        query = query.join(RFI, RFIActivityLink.rfi_id == RFI.id)
        query = query.join(ScheduleActivity, RFIActivityLink.activity_id == ScheduleActivity.id)
        query = query.where(RFI.project_id == project.id, ScheduleActivity.project_id == project.id)
        query = query.where(RFI.status == "open", ScheduleActivity.is_critical.is_(True))
        query = query.order_by(RFI.rfi_number, ScheduleActivity.activity_code)

        rows = db.execute(query).all()
        links = []

        for link, rfi, activity in rows:
            links.append({
                "rfi_number": rfi.rfi_number,
                "rfi_subject": rfi.subject,
                "rfi_status": rfi.status,
                "reported_rfi_impact_days": rfi.schedule_impact_days,
                "activity_code": activity.activity_code,
                "activity_name": activity.name,
                "activity_status": activity.status,
                "is_critical": activity.is_critical,
                "link_source": link.link_source,
                "is_verified": link.is_verified,
                "note": link.note
            })

        return {
            "project_name": project.name,
            "link_count": len(links),
            "links": links
        }