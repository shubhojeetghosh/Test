from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.routes.auth import get_current_user_id
from app.admin_portal.models.student_exam_access import StudentExamAccess


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

    unlocked_set_ids = db.scalars(
        select(StudentExamAccess.exam_set_id)
        .where(
            StudentExamAccess.student_id == current_user_id
        )
    ).all()

    return {
        "unlocked_set_ids": list(unlocked_set_ids)
    }