from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.admin_portal.models.user import User
from app.admin_portal.models.exam_set import ExamSet
from app.admin_portal.models.student_exam_access import StudentExamAccess
from app.admin_portal.routes.auth import get_current_admin


router = APIRouter(
    prefix="/admin/student-access",
    tags=["Admin Student Exam Access"],
)


@router.get("")
def get_student_exam_access(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    records = db.execute(
        select(
            StudentExamAccess.id,
            StudentExamAccess.student_id,
            StudentExamAccess.exam_set_id,
            StudentExamAccess.unlocked_by,
            StudentExamAccess.unlocked_at,
            User.name.label("student_name"),
            User.email.label("student_email"),
            ExamSet.set_number,
            ExamSet.set_name.label("exam_set_title"),
        )
        .join(
            User,
            User.id == StudentExamAccess.student_id,
        )
        .join(
            ExamSet,
            ExamSet.id == StudentExamAccess.exam_set_id,
        )
        .where(User.role.ilike("student"))
        .order_by(StudentExamAccess.unlocked_at.desc())
    ).mappings().all()

    return {
        "total": len(records),
        "records": [
            {
                "id": record["id"],
                "student_id": record["student_id"],
                "student_name": record["student_name"],
                "student_email": record["student_email"],
                "exam_set_id": record["exam_set_id"],
                "set_number": record["set_number"],
                "exam_set_title": record["exam_set_title"],
                "unlocked_by": record["unlocked_by"],
                "unlocked_at": (
                    record["unlocked_at"].isoformat()
                    if isinstance(record["unlocked_at"], datetime)
                    else record["unlocked_at"]
                ),
                "status": "Unlocked",
            }
            for record in records
        ],
    }
