from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import ensure_exam_set_access, get_current_user
from app.models.orm import QuestionModel, OptionModel
from app.schemas.quiz import QuestionResponse, OptionResponse
from app.services.media_storage import resolve_media_urls


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
    response: Response,
    limit: int = Query(default=200, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Returns the questions and options for an exam set.

    Correct answers are intentionally not included.
    """

    ensure_exam_set_access(db, current_user.id, set_id)

    base_query = db.query(QuestionModel).filter(
        QuestionModel.set_id == set_id,
        QuestionModel.status == "PUBLISHED",
    )
    total_count = base_query.count()
    response.headers["X-Total-Count"] = str(total_count)

    if total_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No published questions found for this exam set.",
        )

    questions = (
        base_query
        .order_by(QuestionModel.question_number.asc())
        .offset(offset)
        .limit(limit)
        .all()
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

    media_values = [
        value
        for question in questions
        for value in (question.image_url, question.audio_url)
    ] + [
        value
        for option in all_options
        for value in (option.image_url, option.audio_url)
    ]
    try:
        signed_media = resolve_media_urls(media_values)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Exam media is temporarily unavailable.") from exc

    # Build response
    result = []

    for question in questions:

        options = options_by_question.get(
            question.id,
            []
        )

        result.append(
            QuestionResponse(
                id=str(question.id),
                question_number=question.question_number,
                question_type=str(
                    question.question_type
                ).lower(),
                text=question.question_text or "",
                image_url=signed_media.get(question.image_url, question.image_url),
                audio_url=signed_media.get(question.audio_url, question.audio_url),
                options=[
                    OptionResponse(
                        id=str(option.id),
                        text=option.option_text or "",
                        image_url=signed_media.get(option.image_url, option.image_url),
                        audio_url=signed_media.get(option.audio_url, option.audio_url),
                    )
                    for option in options
                ],
            )
        )

    return result
