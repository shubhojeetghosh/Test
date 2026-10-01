from fastapi import APIRouter, HTTPException, Request, status

from backend.quiz_engine.schemas.schemas import (
    ErrorResponse,
    QuizDetailResponse,
    QuizSummaryResponse,
)

router = APIRouter(
    prefix="/api/quizzes",
    tags=["Quizzes"],
)


@router.get(
    "/",
    response_model=list[QuizSummaryResponse],
    summary="List available quizzes",
)
def list_quizzes(request: Request):
    """
    Returns a summary list of all available exams/quizzes.
    """
    exam_repo = request.app.state.exam_repo
    exams = exam_repo.list_all()

    return [
        QuizSummaryResponse(
            id=exam.id,
            title=exam.title,
            duration_minutes=exam.duration_minutes,
            total_questions=exam.total_questions,
            total_marks=exam.total_marks,
        )
        for exam in exams
    ]


@router.get(
    "/{quiz_id}",
    response_model=QuizDetailResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get quiz details",
)
def get_quiz_detail(quiz_id: str, request: Request):
    """
    Retrieves details for a specific quiz by ID.
    Does NOT reveal question answers.
    """
    exam_repo = request.app.state.exam_repo
    exam = exam_repo.get(quiz_id)

    if exam is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quiz '{quiz_id}' not found.",
        )

    return QuizDetailResponse(
        id=exam.id,
        title=exam.title,
        duration_minutes=exam.duration_minutes,
        total_questions=exam.total_questions,
        marks_per_question=exam.marks_per_question,
        total_marks=exam.total_marks,
    )