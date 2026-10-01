from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, update, text
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.admin_portal.models.exam import Exam
from app.admin_portal.models.exam_set import ExamSet
from app.admin_portal.models.question import Question
from app.admin_portal.models.option import Option
from app.admin_portal.models.user import User
from app.admin_portal.routes.auth import get_current_admin
from app.admin_portal.schemas.exam import ExamCreate, ExamUpdate

router = APIRouter(
    prefix="/admin/exams",
    tags=["Admin Exams"],
)


# =========================
# GET ALL EXAMS
# =========================

@router.get("")
def get_exams(
    current_admin: User = Depends(get_current_admin),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    exams = db.scalars(
        select(Exam).order_by(Exam.id).offset(offset).limit(limit)
    ).all()

    # Get all exam IDs
    exam_ids = [
        exam.id
        for exam in exams
    ]

    # Get all sets belonging to these exams
    exam_sets = []

    if exam_ids:
        exam_sets = db.scalars(
            select(ExamSet)
            .where(
                ExamSet.exam_id.in_(exam_ids)
            )
            .order_by(
                ExamSet.exam_id,
                ExamSet.set_number
            )
        ).all()

    # Group sets by exam_id
    sets_by_exam = {}

    for exam_set in exam_sets:

        sets_by_exam.setdefault(
            exam_set.exam_id,
            []
        ).append(
            {
                "id": exam_set.id,
                "exam_id": exam_set.exam_id,
                "set_number": exam_set.set_number,
                "set_name": exam_set.set_name,
                "created_by": exam_set.created_by,
                "created_at": exam_set.created_at,
            }
        )

    # Build response
    return [
        {
            "id": exam.id,
            "title": exam.title,
            "duration_minutes": exam.duration_minutes,
            "total_questions": exam.total_questions,
            "total_marks": float(exam.total_marks),
            "status": exam.status,
            "created_at": exam.created_at,

            # Include exam sets
            "sets": sets_by_exam.get(
                exam.id,
                []
            ),
        }
        for exam in exams
    ]


# =========================
# GET SINGLE EXAM
# =========================

@router.get("/{exam_id}")
def get_exam(
    exam_id: int,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    exam = db.scalar(
        select(Exam).where(Exam.id == exam_id)
    )

    if exam is None:
        raise HTTPException(
            status_code=404,
            detail="Exam not found",
        )

    return {
        "id": exam.id,
        "title": exam.title,
        "duration_minutes": exam.duration_minutes,
        "total_questions": exam.total_questions,
        "total_marks": float(exam.total_marks),
        "status": exam.status,
        "created_at": exam.created_at,
    }


# =========================
# CREATE EXAM
# =========================

@router.post("", status_code=status.HTTP_201_CREATED)
def create_exam(
    exam_data: ExamCreate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    exam = Exam(
        title=exam_data.title,
        duration_minutes=exam_data.duration_minutes,
        total_questions=exam_data.total_questions,
        total_marks=exam_data.total_marks,
        status=exam_data.status.upper(),
    )

    db.add(exam)
    db.commit()
    db.refresh(exam)

    return {
        "message": "Exam created successfully",
        "exam": {
            "id": exam.id,
            "title": exam.title,
            "duration_minutes": exam.duration_minutes,
            "total_questions": exam.total_questions,
            "total_marks": float(exam.total_marks),
            "status": exam.status,
            "created_at": exam.created_at,
        },
    }


# =========================
# UPDATE EXAM
# =========================

@router.put("/{exam_id}")
def update_exam(
    exam_id: int,
    exam_data: ExamUpdate,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    exam = db.scalar(
        select(Exam).where(Exam.id == exam_id)
    )

    if exam is None:
        raise HTTPException(
            status_code=404,
            detail="Exam not found",
        )

    update_data = exam_data.model_dump(
        exclude_unset=True
    )

    # Normalize status
    if "status" in update_data and update_data["status"]:
        update_data["status"] = update_data["status"].upper()

    # Update exam fields
    for field, value in update_data.items():
        setattr(exam, field, value)

    # If exam is being published,
    # publish all questions belonging to this exam.
    if update_data.get("status") == "PUBLISHED":

        db.execute(
            update(Question)
            .where(Question.exam_id == exam_id)
            .values(status="PUBLISHED")
        )

    db.commit()
    db.refresh(exam)

    return {
        "message": "Exam updated successfully",
        "exam": {
            "id": exam.id,
            "title": exam.title,
            "duration_minutes": exam.duration_minutes,
            "total_questions": exam.total_questions,
            "total_marks": float(exam.total_marks),
            "status": exam.status,
            "created_at": exam.created_at,
        },
    }

# =========================================================
# DELETE EXAM
# =========================================================

@router.delete("/{exam_id}")
def delete_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    exam = db.scalar(
        select(Exam).where(
            Exam.id == exam_id
        )
    )

    if exam is None:
        raise HTTPException(
            status_code=404,
            detail="Exam not found"
        )

    try:

        # -------------------------------------------------
        # 1. GET QUESTION IDS
        # -------------------------------------------------

        question_ids = db.scalars(
            select(Question.id).where(
                Question.exam_id == exam_id
            )
        ).all()

        # -------------------------------------------------
        # 2. DELETE STUDENT ANSWERS
        # -------------------------------------------------
        # Student answers may reference both:
        # - question_id
        # - selected_option_id
        #
        # Therefore they must be deleted BEFORE
        # deleting options and questions.

        if question_ids:

            db.execute(
                text("""
                    DELETE FROM student_answers
                    WHERE question_id IN (
                        SELECT id
                        FROM questions
                        WHERE exam_id = :exam_id
                    )
                """),
                {
                    "exam_id": exam_id
                }
            )

        # -------------------------------------------------
        # 3. DELETE OPTIONS
        # -------------------------------------------------

        if question_ids:

            db.query(Option).filter(
                Option.question_id.in_(question_ids)
            ).delete(
                synchronize_session=False
            )

        # -------------------------------------------------
        # 4. DELETE QUESTIONS
        # -------------------------------------------------

        db.query(Question).filter(
            Question.exam_id == exam_id
        ).delete(
            synchronize_session=False
        )

        # -------------------------------------------------
        # 5. DELETE STUDENT EXAM ACCESS
        # -------------------------------------------------

        db.execute(
            text("""
                DELETE FROM student_exam_access
                WHERE exam_set_id IN (
                    SELECT id
                    FROM exam_sets
                    WHERE exam_id = :exam_id
                )
            """),
            {
                "exam_id": exam_id
            }
        )

        # -------------------------------------------------
        # 6. DELETE EXAM SETS
        # -------------------------------------------------

        db.query(ExamSet).filter(
            ExamSet.exam_id == exam_id
        ).delete(
            synchronize_session=False
        )


        # -------------------------------------------------
        # 7. DELETE EXAM SESSIONS
        # -------------------------------------------------

        db.execute(
            text("""
                DELETE FROM exam_sessions
                WHERE exam_id = :exam_id
            """),
            {
                "exam_id": exam_id
            }
        )

        # -------------------------------------------------
        # 8. DELETE EXAM
        # -------------------------------------------------

        db.delete(exam)

        db.commit()

        return {
            "message": "Exam deleted successfully",
            "exam_id": exam_id,
        }

    except Exception as error:

        db.rollback()

        print(
            f"ERROR deleting exam {exam_id}:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete exam: {str(error)}"
        )
