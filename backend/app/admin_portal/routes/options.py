from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.admin_portal.models.question import Question
from app.admin_portal.models.option import Option
from app.admin_portal.schemas.question import OptionCreate, OptionUpdate


router = APIRouter(
    prefix="/admin/questions",
    tags=["Admin Options"],
)


# =========================
# GET ALL OPTIONS
# =========================

@router.get("/{question_id}/options")
def get_options(
    question_id: int,
    db: Session = Depends(get_db),
):
    question = db.scalar(
        select(Question).where(
            Question.id == question_id
        )
    )

    if question is None:
        raise HTTPException(
            status_code=404,
            detail="Question not found",
        )

    options = db.scalars(
        select(Option)
        .where(Option.question_id == question_id)
        .order_by(Option.id)
    ).all()

    return [
        {
            "id": option.id,
            "question_id": option.question_id,
            "option_label": option.option_label,
            "option_text": option.option_text,
            "image_url": option.image_url,
            "audio_url": option.audio_url,
            "is_correct": option.is_correct,
            "image_id": option.image_id,
        }
        for option in options
    ]


# =========================
# GET SINGLE OPTION
# =========================

@router.get("/{question_id}/options/{option_id}")
def get_option(
    question_id: int,
    option_id: int,
    db: Session = Depends(get_db),
):
    option = db.scalar(
        select(Option).where(
            Option.id == option_id,
            Option.question_id == question_id,
        )
    )

    if option is None:
        raise HTTPException(
            status_code=404,
            detail="Option not found",
        )

    return {
        "id": option.id,
        "question_id": option.question_id,
        "option_label": option.option_label,
        "option_text": option.option_text,
        "image_url": option.image_url,
        "audio_url": option.audio_url,
        "is_correct": option.is_correct,
        "image_id": option.image_id,
    }


# =========================
# CREATE OPTION
# =========================

@router.post(
    "/{question_id}/options",
    status_code=status.HTTP_201_CREATED,
)
def create_option(
    question_id: int,
    option_data: OptionCreate,
    db: Session = Depends(get_db),
):
    question = db.scalar(
        select(Question).where(
            Question.id == question_id
        )
    )

    if question is None:
        raise HTTPException(
            status_code=404,
            detail="Question not found",
        )

    existing_option = db.scalar(
        select(Option).where(
            Option.question_id == question_id,
            Option.option_label == option_data.option_label,
        )
    )

    if existing_option is not None:
        raise HTTPException(
            status_code=400,
            detail="Option label already exists for this question",
        )

    option = Option(
        question_id=question_id,
        option_label=option_data.option_label,
        option_text=option_data.option_text,
        image_url=option_data.image_url,
        audio_url=option_data.audio_url,
        is_correct=option_data.is_correct,
        image_id=option_data.image_id,
    )

    db.add(option)
    db.commit()
    db.refresh(option)

    return {
        "message": "Option created successfully",
        "option": {
            "id": option.id,
            "question_id": option.question_id,
            "option_label": option.option_label,
            "option_text": option.option_text,
            "image_url": option.image_url,
            "audio_url": option.audio_url,
            "is_correct": option.is_correct,
            "image_id": option.image_id,
        },
    }


# =========================
# UPDATE OPTION
# =========================

@router.put("/{question_id}/options/{option_id}")
def update_option(
    question_id: int,
    option_id: int,
    option_data: OptionUpdate,
    db: Session = Depends(get_db),
):
    option = db.scalar(
        select(Option).where(
            Option.id == option_id,
            Option.question_id == question_id,
        )
    )

    if option is None:
        raise HTTPException(
            status_code=404,
            detail="Option not found",
        )

    update_data = option_data.model_dump(
        exclude_unset=True
    )

    if "option_label" in update_data:
        existing_option = db.scalar(
            select(Option).where(
                Option.question_id == question_id,
                Option.option_label
                == update_data["option_label"],
                Option.id != option_id,
            )
        )

        if existing_option is not None:
            raise HTTPException(
                status_code=400,
                detail="Option label already exists for this question",
            )

    for field, value in update_data.items():
        setattr(option, field, value)

    db.commit()
    db.refresh(option)

    return {
        "message": "Option updated successfully",
        "option": {
            "id": option.id,
            "question_id": option.question_id,
            "option_label": option.option_label,
            "option_text": option.option_text,
            "image_url": option.image_url,
            "audio_url": option.audio_url,
            "is_correct": option.is_correct,
            "image_id": option.image_id,
        },
    }


# =========================
# DELETE OPTION
# =========================

@router.delete("/{question_id}/options/{option_id}")
def delete_option(
    question_id: int,
    option_id: int,
    db: Session = Depends(get_db),
):
    option = db.scalar(
        select(Option).where(
            Option.id == option_id,
            Option.question_id == question_id,
        )
    )

    if option is None:
        raise HTTPException(
            status_code=404,
            detail="Option not found",
        )

    db.delete(option)
    db.commit()

    return {
        "message": "Option deleted successfully",
        "option_id": option_id,
    }
    
