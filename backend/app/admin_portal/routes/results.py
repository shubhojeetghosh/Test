from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.admin_portal.models.exam_attempt import ExamSession
from app.admin_portal.models.user import User
from app.admin_portal.models.exam import Exam
from app.admin_portal.routes.auth import get_current_admin
from app.models.orm import QuestionModel, OptionModel, StudentAnswerModel, ResultModel


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

    question_query = select(QuestionModel).where(
        QuestionModel.exam_id == attempt.exam_id
    )
    if attempt.set_id is not None:
        question_query = question_query.where(QuestionModel.set_id == attempt.set_id)
    questions = db.scalars(
        question_query.order_by(QuestionModel.question_number.asc())
    ).all()

    # Get all answers belonging to this exam session.
    student_answers = db.scalars(
        select(StudentAnswerModel)
        .where(
            StudentAnswerModel.attempt_id == attempt.id
        )
    ).all()

    correct_option_by_question = dict(
        db.execute(
            select(OptionModel.question_id, OptionModel.id)
            .where(
                OptionModel.question_id.in_([question.id for question in questions]),
                OptionModel.is_correct.is_(True),
            )
        ).all()
    ) if questions else {}
    return _result_from_rows(questions, student_answers, correct_option_by_question)


def _result_from_rows(questions, student_answers, correct_option_by_question):
    total_questions = len(questions)
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

        correct_option_id = correct_option_by_question.get(question.id)

        if correct_option_id is not None and selected_option_id == correct_option_id:
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


def build_attempt_responses(db: Session, attempts: list[ExamSession]):
    """Build a page of results using a fixed number of queries, not per attempt."""
    if not attempts:
        return []
    user_ids = {attempt.user_id for attempt in attempts}
    exam_ids = {attempt.exam_id for attempt in attempts}
    attempt_ids = {attempt.id for attempt in attempts}
    saved_results = {
        result.attempt_id: result
        for result in db.scalars(
            select(ResultModel).where(ResultModel.attempt_id.in_(attempt_ids))
        ).all()
    }
    user_by_id = {
        user.id: user
        for user in db.scalars(select(User).where(User.id.in_(user_ids))).all()
    }
    exam_by_id = {
        exam.id: exam
        for exam in db.scalars(select(Exam).where(Exam.id.in_(exam_ids))).all()
    }

    scopes = {
        (attempt.exam_id, attempt.set_id)
        for attempt in attempts
    }
    question_query = select(QuestionModel).where(
        or_(*[
            and_(
                QuestionModel.exam_id == exam_id,
                QuestionModel.set_id == set_id
                if set_id is not None
                else QuestionModel.set_id.is_(None),
            )
            for exam_id, set_id in scopes
        ])
    )
    questions = db.scalars(question_query).all()
    questions_by_scope: dict[tuple[int, int | None], list[QuestionModel]] = {}
    for question in questions:
        questions_by_scope.setdefault((question.exam_id, question.set_id), []).append(question)

    question_ids = [question.id for question in questions]
    correct_option_by_question = dict(
        db.execute(
            select(OptionModel.question_id, OptionModel.id).where(
                OptionModel.question_id.in_(question_ids),
                OptionModel.is_correct.is_(True),
            )
        ).all()
    ) if question_ids else {}
    answers_by_attempt: dict[int, list[StudentAnswerModel]] = {}
    for answer in db.scalars(
        select(StudentAnswerModel).where(StudentAnswerModel.attempt_id.in_(attempt_ids))
    ).all():
        answers_by_attempt.setdefault(answer.attempt_id, []).append(answer)

    responses = []
    for attempt in attempts:
        user = user_by_id.get(attempt.user_id)
        exam = exam_by_id.get(attempt.exam_id)
        scoped_questions = questions_by_scope.get((attempt.exam_id, attempt.set_id), [])
        saved = saved_results.get(attempt.id)
        result_summary = (
            {
                "total_questions": saved.total_questions,
                "correct_answers": saved.correct_answers,
                "wrong_answers": saved.wrong_answers,
                "unanswered": saved.unanswered,
                "score": float(saved.score),
                "percentage": float(saved.percentage),
            }
            if saved is not None
            else _result_from_rows(
                scoped_questions,
                answers_by_attempt.get(attempt.id, []),
                correct_option_by_question,
            )
        )
        responses.append({
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
            "result": result_summary,
        })
    return responses


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

    saved = db.scalar(
        select(ResultModel).where(ResultModel.attempt_id == attempt.id)
    )
    attempt_result = (
        {
            "total_questions": saved.total_questions,
            "correct_answers": saved.correct_answers,
            "wrong_answers": saved.wrong_answers,
            "unanswered": saved.unanswered,
            "score": float(saved.score),
            "percentage": float(saved.percentage),
        }
        if saved is not None
        else calculate_attempt_result(db, attempt)
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
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):

    attempts = db.scalars(
        select(ExamSession)
        .order_by(
            ExamSession.id.desc()
        ).offset(offset).limit(limit)
    ).all()

    return build_attempt_responses(db, attempts)


# ============================================================
# GET SINGLE ATTEMPT
# ============================================================

@router.get("/attempts/{attempt_id}")
def get_attempt(
    attempt_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
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
