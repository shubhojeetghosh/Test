from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.database import get_db

from app.admin_portal.models.user import User
from app.admin_portal.models.exam import Exam
from app.admin_portal.models.question import Question
from app.admin_portal.models.exam_attempt import ExamSession
from app.admin_portal.models.result import Result

from app.admin_portal.routes.auth import get_current_admin
from app.admin_portal.core.security import hash_password


router = APIRouter(
    prefix="/admin",
    tags=["Admin Dashboard"],
)


# ============================================================
# ADMIN DASHBOARD
# ============================================================

@router.get("/dashboard")
def dashboard(
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    total_students = db.scalar(
        select(func.count(User.id)).where(
            func.lower(User.role) == "student",
            User.email_verified.is_(True),
        )
    ) or 0

    total_admins = db.scalar(
        select(func.count(User.id)).where(
            User.role == "admin"
        )
    ) or 0

    total_exams = db.scalar(
        select(func.count(Exam.id))
    ) or 0

    total_questions = db.scalar(
        select(func.count(Question.id))
    ) or 0

    total_attempts = db.scalar(
        select(func.count(ExamSession.id))
    ) or 0

    average_score = db.scalar(
        select(func.avg(Result.score))
    )

    return {
        "total_students": total_students,
        "total_admins": total_admins,
        "total_exams": total_exams,
        "total_questions": total_questions,
        "total_attempts": total_attempts,
        "average_score": (
            round(float(average_score), 2)
            if average_score is not None
            else 0
        ),
    }


# ============================================================
# GET STUDENT USERS
# ============================================================

@router.get("/users")
def get_users(
    current_admin: User = Depends(get_current_admin),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    students = db.scalars(
        select(User)
        .where(
            func.lower(User.role) == "student",
            User.email_verified.is_(True),
        )
        .order_by(User.created_at.desc(), User.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    return [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": str(user.role).lower(),
            "status": "Active",
            "created_at": (
                user.created_at.isoformat()
                if user.created_at
                else None
            ),
        }
        for user in students
    ]


# ============================================================
# ADD / CREATE STUDENT USER
# ============================================================

@router.post("/users")
def create_user(
    request: dict,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    name = str(
        request.get("name", "")
    ).strip()

    email = str(
        request.get("email", "")
    ).strip().lower()

    password = str(
        request.get("password", "")
    )

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name is required",
        )

    if len(name) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name cannot exceed 100 characters",
        )

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required",
        )

    if len(email) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email cannot exceed 255 characters",
        )

    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required",
        )

    if len(password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least 6 characters",
        )

    # --------------------------------------------------------
    # CHECK DUPLICATE EMAIL
    # --------------------------------------------------------

    existing_user = db.scalar(
        select(User).where(
            func.lower(User.email) == email
        )
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    # --------------------------------------------------------
    # CREATE STUDENT
    # --------------------------------------------------------

    new_user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role="student",
        student_id=None,
    )

    db.add(new_user)

    db.commit()

    db.refresh(new_user)

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {
        "message": "User created successfully",
        "user": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "role": str(new_user.role).lower(),
            "status": "Active",
            "created_at": (
                new_user.created_at.isoformat()
                if new_user.created_at
                else None
            ),
        },
    }


# ============================================================
# EDIT / UPDATE STUDENT USER
# ============================================================

@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    request: dict,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    # --------------------------------------------------------
    # FIND USER
    # --------------------------------------------------------

    user = db.scalar(
        select(User).where(
            User.id == user_id
        )
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # --------------------------------------------------------
    # ONLY STUDENTS CAN BE EDITED FROM THIS SECTION
    # --------------------------------------------------------

    if str(user.role).lower() != "student":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only student users can be edited here",
        )

    # --------------------------------------------------------
    # GET UPDATED VALUES
    # --------------------------------------------------------

    name = str(
        request.get(
            "name",
            user.name
        )
    ).strip()

    email = str(
        request.get(
            "email",
            user.email
        )
    ).strip().lower()

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name is required",
        )

    if len(name) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name cannot exceed 100 characters",
        )

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required",
        )

    if len(email) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email cannot exceed 255 characters",
        )

    # --------------------------------------------------------
    # CHECK EMAIL BELONGS TO ANOTHER USER
    # --------------------------------------------------------

    existing_user = db.scalar(
        select(User).where(
            func.lower(User.email) == email,
            User.id != user.id,
        )
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Another user already uses this email",
        )

    # --------------------------------------------------------
    # UPDATE USER
    # --------------------------------------------------------

    user.name = name
    user.email = email

    db.commit()

    db.refresh(user)

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return {
        "message": "User updated successfully",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": str(user.role).lower(),
            "status": "Active",
            "created_at": (
                user.created_at.isoformat()
                if user.created_at
                else None
            ),
        },
    }
