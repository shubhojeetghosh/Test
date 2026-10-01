from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.routes.auth import get_current_user_id
from app.models.attempt import AttemptStatus
from app.models.orm import ExamModel, ExamSetModel


router = APIRouter(
    prefix="/api/student",
    tags=["Student Dashboard"],
)


@router.get("/dashboard")
def get_student_dashboard(
    request: Request,
    db: Session = Depends(get_db),
    current_user_id: int = Depends(get_current_user_id),
):
    """
    Return dashboard statistics for the logged-in student.
    """

    attempt_repo = request.app.state.attempt_repo

    # =========================================================
    # AVAILABLE TESTS
    # =========================================================

    tests_available = db.query(ExamSetModel).count()

    # =========================================================
    # GET STUDENT ATTEMPTS
    # =========================================================

    attempts = attempt_repo.list_by_student(
        str(current_user_id)
    )

    completed_attempts = [
        attempt
        for attempt in attempts
        if attempt.status == AttemptStatus.SUBMITTED
    ]

    # =========================================================
    # KEEP ONLY THE LATEST COMPLETED ATTEMPT FOR EACH EXAM
    # =========================================================

    latest_attempt_by_exam = {}

    for attempt in completed_attempts:
        exam_key = str(attempt.exam_id)

        existing = latest_attempt_by_exam.get(exam_key)

        if existing is None:
            latest_attempt_by_exam[exam_key] = attempt
            continue

        existing_date = existing.started_at
        current_date = attempt.started_at

        if current_date and (
            existing_date is None
            or current_date > existing_date
        ):
            latest_attempt_by_exam[exam_key] = attempt

    # =========================================================
    # CALCULATE RESULTS
    # =========================================================

    percentages = []
    recent_results = []

    for attempt in latest_attempt_by_exam.values():

        try:
            exam_id = int(attempt.exam_id)
        except (ValueError, TypeError):
            continue

        exam = (
            db.query(ExamModel)
            .filter(ExamModel.id == exam_id)
            .first()
        )

        if exam is None:
            continue

        questions = list(exam.questions)

        total_marks = 0.0
        score = 0.0
        correct_answers = 0

        # -----------------------------------------------------
        # Map question ID -> selected option ID
        # -----------------------------------------------------

        answer_map = {
            str(answer.question_id): answer.selected_option_id
            for answer in attempt.answers.values()
        }

        # -----------------------------------------------------
        # Calculate score from actual questions/options
        # -----------------------------------------------------

        for question in questions:

            marks = float(question.marks or 0)

            total_marks += marks

            selected_option_id = answer_map.get(
                str(question.id)
            )

            if selected_option_id is None:
                continue

            correct_option = next(
                (
                    option
                    for option in question.options
                    if option.is_correct
                ),
                None,
            )

            if (
                correct_option is not None
                and int(selected_option_id)
                == int(correct_option.id)
            ):
                correct_answers += 1
                score += marks

        # -----------------------------------------------------
        # Calculate percentage
        # -----------------------------------------------------

        if total_marks > 0:
            percentage = (
                score / total_marks
            ) * 100
        else:
            percentage = 0.0

        percentage = round(percentage, 2)

        percentages.append(percentage)

        # -----------------------------------------------------
        # Store recent result
        # -----------------------------------------------------

        recent_results.append(
            {
                "test_name": exam.title,
                "date": (
                    attempt.started_at.isoformat()
                    if attempt.started_at
                    else None
                ),
                "score": round(score, 2),
                "percentage": percentage,
                "correct_answers": correct_answers,
                "result": "Completed",
            }
        )

    # =========================================================
    # COMPLETED TESTS
    # =========================================================

    completed_exam_ids = set(
        latest_attempt_by_exam.keys()
    )

    tests_completed = len(completed_exam_ids)

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

    recent_results.sort(
        key=lambda item: item["date"] or "",
        reverse=True,
    )

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