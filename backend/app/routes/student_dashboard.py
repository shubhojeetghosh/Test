from fastapi import APIRouter, Depends
from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.routes.auth import get_current_user_id
from app.models.orm import (
    ExamModel,
    ExamSessionModel,
    ExamSetModel,
    OptionModel,
    QuestionModel,
    StudentAnswerModel,
)


router = APIRouter(
    prefix="/api/student",
    tags=["Student Dashboard"],
)


@router.get("/dashboard")
def get_student_dashboard(
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Return dashboard statistics for the logged-in student.
    """

    # =========================================================
    # AVAILABLE TESTS
    # =========================================================

    tests_available = db.query(ExamSetModel).count()

    # =========================================================
    # Get the most recent submitted attempt per exam in SQL. This avoids
    # loading every attempt and answer into Python, then issuing one query per
    # exam as student histories grow.
    # =========================================================

    latest_attempts = (
        db.query(
            ExamSessionModel.exam_id.label("exam_id"),
            func.max(ExamSessionModel.id).label("attempt_id"),
        )
        .filter(
            ExamSessionModel.user_id == current_user_id,
            ExamSessionModel.status.in_(("SUBMITTED", "AUTO_SUBMITTED")),
        )
        .group_by(ExamSessionModel.exam_id)
        .subquery()
    )

    result_rows = (
        db.query(
            ExamModel.title.label("test_name"),
            ExamSessionModel.started_at.label("started_at"),
            ExamModel.total_marks.label("total_marks"),
            func.coalesce(
                func.sum(
                    case(
                        (OptionModel.is_correct.is_(True), QuestionModel.marks),
                        else_=0,
                    )
                ),
                0,
            ).label("score"),
            func.coalesce(
                func.sum(case((OptionModel.is_correct.is_(True), 1), else_=0)),
                0,
            ).label("correct_answers"),
        )
        .join(latest_attempts, latest_attempts.c.exam_id == ExamModel.id)
        .join(ExamSessionModel, ExamSessionModel.id == latest_attempts.c.attempt_id)
        .outerjoin(
            StudentAnswerModel,
            StudentAnswerModel.attempt_id == ExamSessionModel.id,
        )
        .outerjoin(
            QuestionModel,
            and_(
                QuestionModel.id == StudentAnswerModel.question_id,
                QuestionModel.exam_id == ExamModel.id,
            ),
        )
        .outerjoin(
            OptionModel,
            and_(
                OptionModel.id == StudentAnswerModel.selected_option_id,
                OptionModel.question_id == StudentAnswerModel.question_id,
            ),
        )
        .group_by(ExamModel.id, ExamSessionModel.id)
        .all()
    )

    percentages = []
    recent_results = []
    for row in result_rows:
        total_marks = float(row.total_marks or 0)
        score = float(row.score or 0)
        percentage = round((score / total_marks) * 100, 2) if total_marks > 0 else 0.0
        percentages.append(percentage)
        recent_results.append({
            "test_name": row.test_name,
            "date": row.started_at.isoformat() if row.started_at else None,
            "score": round(score, 2),
            "percentage": percentage,
            "correct_answers": int(row.correct_answers or 0),
            "result": "Completed",
        })

    # =========================================================
    # COMPLETED TESTS
    # =========================================================

    tests_completed = len(result_rows)

    # =========================================================
    # AVERAGE / BEST SCORE
    # =========================================================

    if percentages:
        average_score = sum(percentages) / len(percentages)
        best_score = max(percentages)
    else:
        average_score = 0.0
        best_score = 0.0

    average_score = round(average_score, 2)
    best_score = round(best_score, 2)

    # =========================================================
    # PROGRESS
    # =========================================================

    if tests_available > 0:
        progress_percentage = (
            tests_completed / tests_available
        ) * 100
    else:
        progress_percentage = 0.0

    # Never allow progress above 100%
    progress_percentage = min(
        round(progress_percentage, 2),
        100.0,
    )

    # =========================================================
    # RECENT RESULTS
    # =========================================================

    recent_results.sort(key=lambda item: item["date"] or "", reverse=True)

    # =========================================================
    # RESPONSE
    # =========================================================

    return {
        "stats": {
            "tests_completed": tests_completed,
            "average_score": average_score,
            "best_score": best_score,
            "tests_available": tests_available,
        },

        "progress": {
            "completed": tests_completed,
            "total": tests_available,
            "percentage": progress_percentage,
            "average_score": average_score,
        },

        "recent_results": recent_results[:5],
    }
