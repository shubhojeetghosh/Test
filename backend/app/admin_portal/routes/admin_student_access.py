from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.admin_portal.models.user import User
from app.admin_portal.models.exam_set import ExamSet
from app.admin_portal.models.student_exam_access import StudentExamAccess
from app.admin_portal.models.exam import Exam
from app.models.student_set_purchase_request import StudentSetPurchaseRequest
from app.admin_portal.routes.auth import get_current_admin


router = APIRouter(
    prefix="/admin/student-access",
    tags=["Admin Student Exam Access"],
)


@router.get("/requests")
def get_pending_set_purchase_requests(
    student_id: int | None = Query(default=None, gt=0),
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    records = db.execute(
        select(
            StudentSetPurchaseRequest.id,
            StudentSetPurchaseRequest.student_id,
            StudentSetPurchaseRequest.exam_set_id,
            StudentSetPurchaseRequest.requested_at,
            User.name.label("student_name"),
            User.email.label("student_email"),
            Exam.title.label("exam_title"),
            ExamSet.set_number,
            ExamSet.set_name.label("exam_set_title"),
        )
        .join(User, User.id == StudentSetPurchaseRequest.student_id)
        .join(ExamSet, ExamSet.id == StudentSetPurchaseRequest.exam_set_id)
        .join(Exam, Exam.id == ExamSet.exam_id)
        .where(
            User.role.ilike("student"),
            StudentSetPurchaseRequest.status == "PENDING",
        )
        .where(
            StudentSetPurchaseRequest.student_id == student_id
            if student_id is not None
            else True
        )
        .order_by(StudentSetPurchaseRequest.requested_at.asc())
    ).mappings().all()

    return {
        "total": len(records),
        "requests": [
            {
                "request_id": row["id"],
                "student_id": row["student_id"],
                "student_name": row["student_name"],
                "student_email": row["student_email"],
                "exam_set_id": row["exam_set_id"],
                "exam_title": row["exam_title"],
                "set_number": row["set_number"],
                "exam_set_title": row["exam_set_title"],
                "requested_at": row["requested_at"].isoformat() if row["requested_at"] else None,
                "status": "Pending payment review",
            }
            for row in records
        ],
    }


@router.post("/requests/{request_id}/reject")
def reject_set_purchase_request(
    request_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    purchase_request = db.scalar(
        select(StudentSetPurchaseRequest).where(
            StudentSetPurchaseRequest.id == request_id
        )
    )
    if purchase_request is None or purchase_request.status != "PENDING":
        raise HTTPException(status_code=404, detail="Pending set request not found")

    purchase_request.status = "REJECTED"
    purchase_request.handled_by = current_admin.id
    purchase_request.handled_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    return {"message": "Set request declined."}


@router.post("/requests/{request_id}/unlock")
def approve_set_purchase_request(
    request_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    purchase_request = db.scalar(
        select(StudentSetPurchaseRequest).where(StudentSetPurchaseRequest.id == request_id)
    )
    if purchase_request is None or purchase_request.status != "PENDING":
        raise HTTPException(status_code=404, detail="Pending set request not found")

    student = db.scalar(select(User).where(
        User.id == purchase_request.student_id,
        User.role.ilike("student"),
    ))
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")

    exam_set = db.scalar(select(ExamSet).where(ExamSet.id == purchase_request.exam_set_id))
    if exam_set is None:
        raise HTTPException(status_code=404, detail="Requested exam set no longer exists")
    if exam_set.set_number == 1:
        raise HTTPException(status_code=400, detail="Set 1 is free and cannot be unlocked")

    access = db.scalar(select(StudentExamAccess).where(
        StudentExamAccess.student_id == student.id,
        StudentExamAccess.exam_set_id == exam_set.id,
    ))
    if access is None:
        db.add(StudentExamAccess(
            student_id=student.id,
            exam_set_id=exam_set.id,
            unlocked_by=current_admin.id,
        ))

    purchase_request.status = "UNLOCKED"
    purchase_request.handled_by = current_admin.id
    purchase_request.handled_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()

    return {
        "message": "Payment-approved set unlocked for the student.",
        "student_id": student.id,
        "exam_set_id": exam_set.id,
    }


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
