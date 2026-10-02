from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models import User
from app.admin_portal.models.exam_set import ExamSet
from app.admin_portal.models.student_exam_access import StudentExamAccess
from app.admin_portal.models.exam import Exam


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


def ensure_exam_set_access(db: Session, student_id: int, set_id: int) -> ExamSet:
    """Return an exam set only when the student is entitled to access it."""
    exam_set = db.scalar(select(ExamSet).where(ExamSet.id == set_id))
    if exam_set is None:
        raise HTTPException(status_code=404, detail="Exam set not found.")

    exam = db.scalar(select(Exam).where(Exam.id == exam_set.exam_id))
    if exam is None or str(exam.status).strip().upper() != "PUBLISHED":
        raise HTTPException(status_code=404, detail="Exam set not found.")

    if exam_set.set_number != 1:
        access = db.scalar(
            select(StudentExamAccess.id).where(
                StudentExamAccess.student_id == student_id,
                StudentExamAccess.exam_set_id == set_id,
            )
        )
        if access is None:
            raise HTTPException(
                status_code=403,
                detail="This exam set has not been unlocked for your account.",
            )

    return exam_set
