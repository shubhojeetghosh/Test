from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
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


class UnlockExamSetsRequest(BaseModel):
    student_id: int
    exam_set_ids: list[int] = Field(min_length=1)


@router.post("/unlock")
def unlock_exam_sets(
    request: UnlockExamSetsRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    student = db.scalar(
        select(User).where(
            User.id == request.student_id,
            User.role.ilike("student"),
        )
    )

    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    requested_ids = set(request.exam_set_ids)

    exam_sets = db.scalars(
        select(ExamSet).where(ExamSet.id.in_(requested_ids))
    ).all()

    if len(exam_sets) != len(requested_ids):
        raise HTTPException(
            status_code=404,
            detail="One or more exam sets were not found",
        )

    if any(exam_set.set_number == 1 for exam_set in exam_sets):
        raise HTTPException(
            status_code=400,
            detail="Set 1 is free and cannot be unlocked",
        )

    existing_access = db.scalars(
        select(StudentExamAccess).where(
            StudentExamAccess.student_id == request.student_id,
            StudentExamAccess.exam_set_id.in_(requested_ids),
        )
    ).all()

    existing_ids = {access.exam_set_id for access in existing_access}
    new_records = []

    for exam_set in exam_sets:
        if exam_set.id not in existing_ids:
            new_records.append(
                StudentExamAccess(
                    student_id=request.student_id,
                    exam_set_id=exam_set.id,
                    unlocked_by=current_admin.id,
                )
            )

    if new_records:
        db.add_all(new_records)
        db.commit()

    return {
        "message": "Exam sets processed successfully",
        "student_id": request.student_id,
        "newly_unlocked_exam_set_ids": [
            record.exam_set_id for record in new_records
        ],
        "already_unlocked_exam_set_ids": sorted(existing_ids),
        "total_newly_unlocked": len(new_records),
    }

@router.delete("/{student_id}/{exam_set_id}")
def lock_exam_set(
    student_id: int,
    exam_set_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    # Check that the student exists
    student = db.scalar(
        select(User).where(
            User.id == student_id,
            User.role.ilike("student"),
        )
    )

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found",
        )

    # Set 1 is free and is not managed by the access system
    exam_set = db.scalar(
        select(ExamSet).where(
            ExamSet.id == exam_set_id
        )
    )

    if exam_set is None:
        raise HTTPException(
            status_code=404,
            detail="Exam set not found",
        )

    if exam_set.set_number == 1:
        raise HTTPException(
            status_code=400,
            detail="Set 1 is free and cannot be locked",
        )

    # Find the student's access record
    access = db.scalar(
        select(StudentExamAccess).where(
            StudentExamAccess.student_id == student_id,
            StudentExamAccess.exam_set_id == exam_set_id,
        )
    )

    if access is None:
        raise HTTPException(
            status_code=404,
            detail="Quiz is already locked for this student",
        )

    # Remove the access record
    db.delete(access)
    db.commit()

    return {
        "message": "Exam set locked successfully",
        "student_id": student_id,
        "exam_set_id": exam_set_id,
    }