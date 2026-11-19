from sqlalchemy import select

from app.db.models import Project, RFI, RFIActivityLink, ScheduleActivity
from app.db.session import SessionLocal


def main():
    with SessionLocal.begin() as db:
        project = db.scalar(select(Project).where(Project.name == "Demo Boston Office Tower"))

        if project is None:
            raise ValueError("Demo project not found")

        rfi = db.scalar(select(RFI).where(RFI.project_id == project.id, RFI.rfi_number == "RFI-037"))
        activity = db.scalar(select(ScheduleActivity).where(ScheduleActivity.project_id == project.id, ScheduleActivity.activity_code == "MEP-100"))

        if rfi is None or activity is None:
            raise ValueError("Demo RFI or schedule activity not found")

        link = db.get(RFIActivityLink, (rfi.id, activity.id))

        if link is None:
            link = RFIActivityLink(rfi_id=rfi.id, activity_id=activity.id, link_source="demo_manual", note="Illustrative association for testing; not verified evidence of causation.", is_verified=False)
            db.add(link)
            print("Created demo association: RFI-037 -> MEP-100")
        else:
            print("Demo association already exists")


if __name__ == "__main__":
    main()