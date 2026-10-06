from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import User
from app.admin_portal.models.exam_set import ExamSet
from app.admin_portal.models.student_exam_access import StudentExamAccess
from app.admin_portal.models.exam import Exam as AdminExam
from app.models.orm import ExamModel, ExamSessionModel


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        user_id = int(user_id)
    except Exception:
        raise credentials_exception

    user = db.scalar(select(User).where(User.id == user_id))

    if user is None:
        raise credentials_exception
    if str(user.role).strip().lower() != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student account required",
        )

    return user


def latest_completed_set_attempt(db: Session, student_id: int, set_id: int):
    return db.scalar(
        select(
            func.max(
                func.coalesce(
                    ExamSessionModel.submitted_at,
                    ExamSessionModel.started_at,
                )
            )
        ).where(
            ExamSessionModel.user_id == student_id,
            ExamSessionModel.set_id == set_id,
            ExamSessionModel.status.in_(("SUBMITTED", "AUTO_SUBMITTED")),
        )
    )


def consume_paid_exam_set_access(
    db: Session, student_id: int, set_id: int | None
) -> bool:
    """Remove the paid-set entitlement when the student submits that set."""
    if set_id is None:
        return False

    set_number = db.scalar(
        select(ExamSet.set_number).where(ExamSet.id == set_id)
    )
    if set_number is None or set_number == 1:
        return False

    result = db.execute(
        delete(StudentExamAccess).where(
            StudentExamAccess.student_id == student_id,
            StudentExamAccess.exam_set_id == set_id,
        )
    )
    return bool(result.rowcount)


def _utc_naive(value: datetime) -> datetime:
    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    return value


def ensure_exam_set_access(db: Session, student_id: int, set_id: int) -> ExamSet:
    """Return a set only when it is unlocked and has not been consumed."""
    exam_set = db.scalar(select(ExamSet).where(ExamSet.id == set_id))
    if exam_set is None:
        raise HTTPException(status_code=404, detail="Exam set not found.")

    exam = db.scalar(select(AdminExam).where(AdminExam.id == exam_set.exam_id))
    if exam is None or str(exam.status).strip().upper() != "PUBLISHED":
        raise HTTPException(status_code=404, detail="Exam set not found.")

    access = None
    if exam_set.set_number != 1:
        access = db.scalar(
            select(StudentExamAccess).where(
                StudentExamAccess.student_id == student_id,
                StudentExamAccess.exam_set_id == set_id,
            )
        )

    completed_at = latest_completed_set_attempt(db, student_id, set_id)

    # Expire a timed-out in-progress attempt here too, so a student cannot
    # restart the same set before the timer-status endpoint is called.
    active_record = db.execute(
        select(ExamSessionModel, ExamModel.duration_minutes)
        .join(ExamModel, ExamModel.id == ExamSessionModel.exam_id)
        .where(
            ExamSessionModel.user_id == student_id,
            ExamSessionModel.set_id == set_id,
            ExamSessionModel.status == "IN_PROGRESS",
        )
        .order_by(ExamSessionModel.id.desc())
        .with_for_update()
    ).first()
    if active_record is not None:
        active_session, duration_minutes = active_record
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        expires_at = _utc_naive(active_session.started_at) + timedelta(
            minutes=int(duration_minutes)
        )
        if now >= expires_at:
            active_session.status = "AUTO_SUBMITTED"
            active_session.submitted_at = now
            consume_paid_exam_set_access(db, student_id, set_id)
            db.commit()
            completed_at = now
            access = None

    already_used = completed_at is not None and (
        exam_set.set_number == 1
        or access is None
        or _utc_naive(completed_at) >= _utc_naive(access.unlocked_at)
    )
    if already_used:
        detail = (
            "You have already completed the free test set."
            if exam_set.set_number == 1
            else "You have already taken this test set. Purchase access again to take it again."
        )
        raise HTTPException(status_code=403, detail=detail)

    if exam_set.set_number != 1 and access is None:
        raise HTTPException(
            status_code=403,
            detail="This exam set has not been unlocked for your account.",
        )

    return exam_set
