from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.admin_portal.models.user import User
from app.admin_portal.core.security import hash_password
from app.admin_portal.routes.auth import get_current_admin


router = APIRouter(
    prefix="/admin/students",
    tags=["Admin Students"],
)


# =========================================================
# REQUEST SCHEMAS
# =========================================================

class StudentCreateRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    student_id: int | None = None


class StudentUpdateRequest(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    student_id: int | None = None
    password: str | None = None


# =========================================================
# HELPER
# =========================================================

def student_response(student: User):
    return {
        "id": student.id,
        "name": student.name,
        "email": student.email,
        "student_id": student.student_id,
        "created_at": student.created_at,
    }


# =========================================================
# GET ALL STUDENTS
# =========================================================

@router.get("")
def get_students(
    current_admin: User = Depends(get_current_admin),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    students = db.scalars(
        select(User)
        .where(
            func.lower(func.trim(User.role)) == "student",
        )
        .order_by(User.id)
        .offset(offset)
        .limit(limit)
    ).all()

    return [
        student_response(student)
        for student in students
    ]


# =========================================================
# GET SINGLE STUDENT
# =========================================================

@router.get("/{student_id}")
def get_student(
    student_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    student = db.scalar(
        select(User).where(
            User.id == student_id,
            func.lower(func.trim(User.role)) == "student",
        )
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    return student_response(student)


# =========================================================
# CREATE STUDENT
# =========================================================

@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
def create_student(
    request: StudentCreateRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    name = request.name.strip()
    email = str(request.email).strip().lower()
    password = request.password

    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name is required",
        )

    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least 8 characters",
        )

    if len(password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at most 72 UTF-8 bytes",
        )

    existing_user = db.scalar(
        select(User).where(
            func.lower(User.email) == email
        )
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )

    if request.student_id is not None:
        existing_student_id = db.scalar(
            select(User).where(
                User.student_id == request.student_id
            )
        )

        if existing_student_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student ID already exists",
            )

    student = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role="STUDENT",
        student_id=request.student_id,
        created_at=datetime.utcnow(),
    )

    db.add(student)
    db.commit()
    db.refresh(student)

    return {
        "message": "Student created successfully",
        "student": student_response(student),
    }


# =========================================================
# UPDATE STUDENT
# =========================================================

@router.put("/{student_id}")
def update_student(
    student_id: int,
    request: StudentUpdateRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    student = db.scalar(
        select(User).where(
            User.id == student_id,
            func.lower(User.role) == "student",
        )
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    if request.name is not None:
        name = request.name.strip()

        if not name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Name cannot be empty",
            )

        student.name = name

    if request.email is not None:
        email = str(request.email).strip().lower()

        existing_user = db.scalar(
            select(User).where(
                func.lower(User.email) == email,
                User.id != student_id,
            )
        )

        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists",
            )

        student.email = email

    if request.student_id is not None:
        existing_student_id = db.scalar(
            select(User).where(
                User.student_id == request.student_id,
                User.id != student_id,
            )
        )

        if existing_student_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student ID already exists",
            )

        student.student_id = request.student_id

    if request.password is not None:
        if len(request.password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least 8 characters",
            )
        if len(request.password.encode("utf-8")) > 72:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at most 72 UTF-8 bytes",
            )

        student.password_hash = hash_password(
            request.password
        )

    db.commit()
    db.refresh(student)

    return {
        "message": "Student updated successfully",
        "student": student_response(student),
    }


# =========================================================
# DELETE STUDENT
# =========================================================

@router.delete("/{student_id}")
def delete_student(
    student_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    student = db.scalar(
        select(User).where(
            User.id == student_id,
            func.lower(User.role) == "student",
        )
    )

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    db.delete(student)
    db.commit()

    return {
        "message": "Student deleted successfully",
        "student_id": student_id,
    }
