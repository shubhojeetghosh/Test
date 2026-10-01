from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.admin_portal.models.exam import Exam
from app.admin_portal.models.exam_set import ExamSet
from app.admin_portal.models.question import Question
from app.admin_portal.models.option import Option
from app.admin_portal.schemas.question import (
    QuestionCreate,
    QuestionUpdate,
)


router = APIRouter(
    prefix="/admin",
    tags=["Admin Questions"]
)


# =========================
# GET ALL QUESTIONS
# =========================

@router.get("/exams/{exam_id}/questions")
def get_questions(
    exam_id: int,
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

    questions = db.scalars(
        select(Question)
        .where(Question.exam_id == exam_id)
        .order_by(Question.question_number)
    ).all()

    result = []

    for question in questions:
        options = db.scalars(
            select(Option)
            .where(Option.question_id == question.id)
            .order_by(Option.id)
        ).all()

        result.append({
            "id": question.id,
            "exam_id": question.exam_id,
            "question_number": question.question_number,
            "question_type": question.question_type,
            "question_text": question.question_text,
            "image_url": question.image_url,
            "audio_url": question.audio_url,
            "marks": float(question.marks),
            "created_at": question.created_at,
            "created_by": question.created_by,
            "set_id": question.set_id,
            "status": question.status,
            "options": [
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
            ],
        })

    return result


# =========================
# GET SINGLE QUESTION
# =========================

@router.get("/questions/{question_id}")
def get_question(
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
        .where(Option.question_id == question.id)
        .order_by(Option.id)
    ).all()

    return {
        "id": question.id,
        "exam_id": question.exam_id,
        "question_number": question.question_number,
        "question_type": question.question_type,
        "question_text": question.question_text,
        "image_url": question.image_url,
        "audio_url": question.audio_url,
        "marks": float(question.marks),
        "created_at": question.created_at,
        "created_by": question.created_by,
        "set_id": question.set_id,
        "status": question.status,
        "options": [
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
        ],
    }


# =========================
# CREATE QUESTION
# =========================

@router.post(
    "/exams/{exam_id}/questions",
    status_code=status.HTTP_201_CREATED,
)
def create_question(
    exam_id: int,
    question_data: QuestionCreate,
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

    if question_data.exam_id != exam_id:
        raise HTTPException(
            status_code=400,
            detail="Question exam_id does not match URL exam_id",
        )

    if question_data.set_id is not None:
        exam_set = db.scalar(
            select(ExamSet).where(
                ExamSet.id == question_data.set_id,
                ExamSet.exam_id == exam_id,
            )
        )

        if exam_set is None:
            raise HTTPException(
                status_code=400,
                detail="Exam set does not belong to this exam",
            )

    existing_question = db.scalar(
        select(Question).where(
            Question.exam_id == exam_id,
            Question.question_number
            == question_data.question_number,
        )
    )

    if existing_question is not None:
        raise HTTPException(
            status_code=400,
            detail="Question number already exists for this exam",
        )

    question = Question(
        exam_id=exam_id,
        question_number=question_data.question_number,
        question_type=question_data.question_type,
        question_text=question_data.question_text,
        image_url=question_data.image_url,
        audio_url=question_data.audio_url,
        marks=question_data.marks,
        created_by=question_data.created_by,
        set_id=question_data.set_id,
        status=question_data.status,
    )

    db.add(question)
    db.flush()

    for option_data in question_data.options:
        option = Option(
            question_id=question.id,
            option_label=option_data.option_label,
            option_text=option_data.option_text,
            image_url=option_data.image_url,
            audio_url=option_data.audio_url,
            is_correct=option_data.is_correct,
            image_id=option_data.image_id,
        )

        db.add(option)

    db.commit()
    db.refresh(question)

    return {
        "message": "Question created successfully",
        "question_id": question.id,
    }


# =========================
# UPDATE QUESTION
# =========================

@router.put("/questions/{question_id}")
def update_question(
    question_id: int,
    question_data: QuestionUpdate,
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

    update_data = question_data.model_dump(
        exclude_unset=True
    )

    if "set_id" in update_data:
        if update_data["set_id"] is not None:
            exam_set = db.scalar(
                select(ExamSet).where(
                    ExamSet.id == update_data["set_id"],
                    ExamSet.exam_id == question.exam_id,
                )
            )

            if exam_set is None:
                raise HTTPException(
                    status_code=400,
                    detail="Exam set does not belong to this exam",
                )

    if "question_number" in update_data:
        existing_question = db.scalar(
            select(Question).where(
                Question.exam_id == question.exam_id,
                Question.question_number
                == update_data["question_number"],
                Question.id != question_id,
            )
        )

        if existing_question is not None:
            raise HTTPException(
                status_code=400,
                detail="Question number already exists for this exam",
            )

    for field, value in update_data.items():
        setattr(question, field, value)

    db.commit()
    db.refresh(question)

    return {
        "message": "Question updated successfully",
        "question_id": question.id,
    }


# =========================
# DELETE QUESTION
# =========================

@router.delete("/questions/{question_id}")
def delete_question(
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
        select(Option).where(
            Option.question_id == question_id
        )
    ).all()

    for option in options:
        db.delete(option)

    db.delete(question)
    db.commit()

    return {
        "message": "Question deleted successfully",
        "question_id": question_id,
    }


