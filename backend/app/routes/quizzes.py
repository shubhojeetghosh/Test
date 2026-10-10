from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models.orm import ExamModel, ExamSetModel

from app.schemas.quiz import (
    ErrorResponse,
    ExamSetSummaryResponse,
    QuizDetailResponse,
    QuizSummaryResponse,
)


router = APIRouter(
    prefix="/api/quizzes",
    tags=["Quizzes"],
)


@router.get(
    "",
    response_model=list[QuizSummaryResponse],
    summary="List available quizzes",
)
@router.get(
    "/",
    response_model=list[QuizSummaryResponse],
    summary="List available quizzes",
)
def list_quizzes(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Returns exams and their exam sets from the PostgreSQL database.
    """

    exams = (
        db.query(ExamModel)
        .options(selectinload(ExamModel.sets))
        .filter(ExamModel.status == "PUBLISHED")
        .order_by(ExamModel.id.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    response = []

    for exam in exams:
        exam_sets = sorted(exam.sets, key=lambda item: item.set_number)

        response.append(
            QuizSummaryResponse(
                id=str(exam.id),
                title=exam.title,
                duration_minutes=exam.duration_minutes,
                total_questions=exam.total_questions,
                total_marks=float(exam.total_marks),
                sets=[
                    ExamSetSummaryResponse(
                        id=exam_set.id,
                        exam_id=exam_set.exam_id,
                        set_number=exam_set.set_number,
                        set_name=exam_set.set_name,
                    )
                    for exam_set in exam_sets
                ],
            )
        )

    return response


@router.get(
    "/{quiz_id}",
    response_model=QuizDetailResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get quiz details",
)
def get_quiz_detail(
    quiz_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieves details for a specific quiz.
    """

    exam = (
        db.query(ExamModel)
        .filter(
            ExamModel.id == quiz_id,
            ExamModel.status == "PUBLISHED",
        )
        .first()
    )

    if exam is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quiz '{quiz_id}' not found.",
        )

    marks_per_question = (
        float(exam.total_marks) / exam.total_questions
        if exam.total_questions
        else 0
    )

    return QuizDetailResponse(
        id=str(exam.id),
        title=exam.title,
        duration_minutes=exam.duration_minutes,
        total_questions=exam.total_questions,
        marks_per_question=marks_per_question,
        total_marks=float(exam.total_marks),
    )
