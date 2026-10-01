from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.orm import QuestionModel, OptionModel
from app.schemas.quiz import QuestionResponse, OptionResponse


router = APIRouter(
    prefix="/api/exam-sets",
    tags=["Student Exams"],
)


@router.get(
    "/{set_id}/questions",
    response_model=list[QuestionResponse],
    summary="Get questions for an exam set",
)
def get_set_questions(
    set_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Returns the questions and options for an exam set.

    Correct answers are intentionally not included.
    """

    # Get all published questions in ONE query
    questions = (
        db.query(QuestionModel)
        .filter(
            QuestionModel.set_id == set_id,
            QuestionModel.status == "PUBLISHED",
        )
        .order_by(QuestionModel.question_number.asc())
        .all()
    )

    if not questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No published questions found for this exam set.",
        )

    # Get all options for all questions in ONE query
    question_ids = [question.id for question in questions]

    all_options = (
        db.query(OptionModel)
        .filter(
            OptionModel.question_id.in_(question_ids)
        )
        .order_by(
            OptionModel.question_id.asc(),
            OptionModel.option_label.asc(),
        )
        .all()
    )

    # Group options by question ID
    options_by_question = {}

    for option in all_options:
        options_by_question.setdefault(
            option.question_id,
            []
        ).append(option)

    # Build response
    response = []

    for question in questions:

        options = options_by_question.get(
            question.id,
            []
        )

        response.append(
            QuestionResponse(
                id=str(question.id),
                question_number=question.question_number,
                question_type=str(
                    question.question_type
                ).lower(),
                text=question.question_text or "",
                image_url=question.image_url,
                audio_url=question.audio_url,
                options=[
                    OptionResponse(
                        id=str(option.id),
                        text=option.option_text or "",
                        audio_url=option.audio_url,
                    )
                    for option in options
                ],
            )
        )

    return response