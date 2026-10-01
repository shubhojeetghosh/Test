from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.admin_portal.models.exam_attempt import ExamSession
from app.admin_portal.models.user import User
from app.admin_portal.models.exam import Exam
from app.admin_portal.routes.auth import get_current_admin
from app.models.orm import QuestionModel, OptionModel, StudentAnswerModel


router = APIRouter(
    prefix="/admin",
    tags=["Admin Results"],
)


# ============================================================
# CALCULATE RESULT FROM EXAM SESSION + STUDENT ANSWERS
# ============================================================

def calculate_attempt_result(
    db: Session,
    attempt: ExamSession,
):
    """
    Calculate the result directly from the actual exam session
    and student answers.

    We intentionally do NOT use the Result table here because
    results.attempt_id currently has a foreign-key mismatch with
    the application's exam_sessions table.
    """

    questions = db.scalars(
        select(QuestionModel)
        .where(
            QuestionModel.exam_id == attempt.exam_id
        )
        .order_by(
            QuestionModel.question_number.asc()
        )
    ).all()

    total_questions = len(questions)

    # Get all answers belonging to this exam session.
    student_answers = db.scalars(
        select(StudentAnswerModel)
        .where(
            StudentAnswerModel.attempt_id == attempt.id
        )
    ).all()

    answer_map = {
        answer.question_id: answer.selected_option_id
        for answer in student_answers
    }

    correct_answers = 0
    wrong_answers = 0
    unanswered = 0
    score = 0.0

    for question in questions:

        selected_option_id = answer_map.get(
            question.id
        )

        # No answer selected.
        if selected_option_id is None:
            unanswered += 1
            continue

        correct_option = db.scalar(
            select(OptionModel)
            .where(
                OptionModel.question_id == question.id,
                OptionModel.is_correct.is_(True),
            )
        )

        if (
            correct_option is not None
            and selected_option_id == correct_option.id
        ):
            correct_answers += 1

            # Use the question's marks when available.
            marks = getattr(
                question,
                "marks",
                None,
            )

            try:
                score += float(marks or 0)
            except (TypeError, ValueError):
                score += 0.0

        else:
            wrong_answers += 1

    # Calculate total marks.
    total_marks = 0.0

    for question in questions:

        marks = getattr(
            question,
            "marks",
            None,
        )

        try:
            total_marks += float(marks or 0)
        except (TypeError, ValueError):
            pass

    if total_marks > 0:
        percentage = (
            score / total_marks
        ) * 100
    elif total_questions > 0:
        percentage = (
            correct_answers /
            total_questions
        ) * 100
    else:
        percentage = 0.0

    return {
        "total_questions": total_questions,
        "correct_answers": correct_answers,
        "wrong_answers": wrong_answers,
        "unanswered": unanswered,
        "score": round(score, 2),
        "percentage": round(
            percentage,
            2,
        ),
    }


# ============================================================
# BUILD ATTEMPT RESPONSE
# ============================================================

def build_attempt_response(
    db: Session,
    attempt: ExamSession,
):
    user = db.scalar(
        select(User).where(
            User.id == attempt.user_id
        )
    )

    exam = db.scalar(
        select(Exam).where(
            Exam.id == attempt.exam_id
        )
    )

    attempt_result = calculate_attempt_result(
        db,
        attempt,
    )

    return {
        "attempt_id": attempt.id,

        "student": {
            "id": user.id if user else None,
            "name": user.name if user else None,
            "email": user.email if user else None,
        },

        "exam": {
            "id": exam.id if exam else None,
            "title": exam.title if exam else None,
        },

        "started_at": attempt.started_at,

        "submitted_at": attempt.submitted_at,

        "status": attempt.status,

        "result": attempt_result,
    }


# ============================================================
# GET ALL EXAM ATTEMPTS
# ============================================================

@router.get("/attempts")
def get_attempts(
    current_admin=Depends(get_current_admin),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):

    attempts = db.scalars(
        select(ExamSession)
        .order_by(
            ExamSession.id.desc()
        ).offset(offset).limit(limit)
    ).all()

    return [
        build_attempt_response(
            db,
            attempt,
        )
        for attempt in attempts
    ]


# ============================================================
# GET SINGLE ATTEMPT
# ============================================================

@router.get("/attempts/{attempt_id}")
def get_attempt(
    attempt_id: int,
    db: Session = Depends(get_db),
):

    attempt = db.scalar(
        select(ExamSession).where(
            ExamSession.id == attempt_id
        )
    )

    if attempt is None:
        raise HTTPException(
            status_code=404,
            detail="Exam attempt not found",
        )

    return build_attempt_response(
        db,
        attempt,
    )
