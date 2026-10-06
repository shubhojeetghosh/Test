from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.routes.auth import get_current_user_id
from app.admin_portal.models.exam_set import ExamSet
from app.admin_portal.models.student_exam_access import StudentExamAccess
from app.models.orm import ExamSessionModel


router = APIRouter(
    prefix="/api/student",
    tags=["Student Access"],
)


@router.get("/access")
def get_student_access(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Return the exam sets unlocked for the currently logged-in student.
    """

    access_records = db.scalars(
        select(StudentExamAccess).where(
            StudentExamAccess.student_id == current_user_id
        )
    ).all()
    access_by_set = {record.exam_set_id: record for record in access_records}

    completed_rows = db.execute(
        select(
            ExamSessionModel.set_id,
            func.max(
                func.coalesce(
                    ExamSessionModel.submitted_at,
                    ExamSessionModel.started_at,
                )
            ).label("completed_at"),
        )
        .where(
            ExamSessionModel.user_id == current_user_id,
            ExamSessionModel.set_id.is_not(None),
            ExamSessionModel.status.in_(("SUBMITTED", "AUTO_SUBMITTED")),
        )
        .group_by(ExamSessionModel.set_id)
    ).all()
    completed_at_by_set = {set_id: completed_at for set_id, completed_at in completed_rows}

    set_numbers = dict(
        db.execute(
            select(ExamSet.id, ExamSet.set_number).where(
                ExamSet.id.in_(set(completed_at_by_set) | set(access_by_set))
            )
        ).all()
    ) if completed_at_by_set or access_by_set else {}

    def as_utc_naive(value: datetime) -> datetime:
        if value.tzinfo is not None:
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    used_set_ids = set()
    unlocked_set_ids = set()
    consumed_access = []

    for set_id in set(completed_at_by_set.keys() | access_by_set.keys()):
        access = access_by_set.get(set_id)
        completed_at = completed_at_by_set.get(set_id)
        set_number = set_numbers.get(set_id)

        if completed_at is not None and (
            set_number == 1
            or access is None
            or as_utc_naive(completed_at) >= as_utc_naive(access.unlocked_at)
        ):
            used_set_ids.add(set_id)
            if access is not None:
                consumed_access.append(access)
        elif access is not None:
            unlocked_set_ids.add(set_id)

    for access in consumed_access:
        db.delete(access)
    if consumed_access:
        db.commit()

    return {
        "unlocked_set_ids": sorted(unlocked_set_ids),
        "used_set_ids": sorted(used_set_ids),
    }
