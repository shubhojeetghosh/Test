from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, or_, select
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
from app.admin_portal.models.user import User
from app.admin_portal.routes.auth import get_current_admin
from app.services.media_storage import (
    create_signed_upload,
)


router = APIRouter(
    prefix="/admin",
    tags=["Admin Questions"]
)


class MediaUploadUrlRequest(BaseModel):
    filename: str
    content_type: str


@router.post("/media/upload-url")
def create_exam_media_upload_url(
    payload: MediaUploadUrlRequest,
    current_admin: User = Depends(get_current_admin),
):
    allowed_types = {
        "image/jpeg", "image/png", "image/webp", "image/gif",
        "audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav",
        "audio/ogg", "audio/webm", "audio/mp4", "audio/aac",
    }
    content_type = payload.content_type.lower().strip()
    if content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Choose a supported image or audio file.")
    if not payload.filename or len(payload.filename) > 255:
        raise HTTPException(status_code=400, detail="Invalid media filename.")
    try:
        upload_url, storage_path = create_signed_upload(payload.filename)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"upload_url": upload_url, "storage_path": storage_path}


# =========================
# GET ALL QUESTIONS
# =========================

@router.get("/exams/{exam_id}/questions")
def get_questions(
    exam_id: int,
    limit: int = Query(default=200, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
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
        .offset(offset)
        .limit(limit)
    ).all()

    result = []

    question_ids = [question.id for question in questions]
    options_by_question: dict[int, list[Option]] = {}
    if question_ids:
        options = db.scalars(
            select(Option)
            .where(Option.question_id.in_(question_ids))
            .order_by(Option.question_id, Option.id)
        ).all()
        for option in options:
            options_by_question.setdefault(option.question_id, []).append(option)

    for question in questions:
        options = options_by_question.get(question.id, [])

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
    current_admin: User = Depends(get_current_admin),
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
    current_admin: User = Depends(get_current_admin),
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
            Question.set_id == question_data.set_id,
            Question.question_number
            == question_data.question_number,
        )
    )

    if existing_question is not None:
        raise HTTPException(
            status_code=400,
            detail="Question number already exists in this set.",
        )

    question_count = db.scalar(
        select(func.count(Question.id)).where(
            Question.exam_id == exam_id,
            Question.set_id == question_data.set_id
            if question_data.set_id is not None
            else Question.set_id.is_(None),
        )
    ) or 0
    if question_count >= 2000:
        raise HTTPException(status_code=413, detail="An exam set cannot exceed 2,000 questions.")

    question = Question(
        exam_id=exam_id,
        question_number=question_data.question_number,
        question_type=question_data.question_type,
        question_text=question_data.question_text,
        image_url=question_data.image_url,
        audio_url=question_data.audio_url,
        marks=question_data.marks,
        created_by=current_admin.id,
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


@router.post(
    "/exams/{exam_id}/questions/bulk",
    status_code=status.HTTP_201_CREATED,
)
def bulk_create_questions(
    exam_id: int,
    questions_data: list[QuestionCreate],
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Insert a set of questions and options in one bounded transaction."""
    if not questions_data or len(questions_data) > 2000:
        raise HTTPException(status_code=400, detail="Submit between 1 and 2,000 questions.")
    if any(question.exam_id != exam_id for question in questions_data):
        raise HTTPException(status_code=400, detail="A question references a different exam.")

    exam = db.scalar(select(Exam).where(Exam.id == exam_id))
    if exam is None:
        raise HTTPException(status_code=404, detail="Exam not found.")

    set_ids = {question.set_id for question in questions_data if question.set_id is not None}
    if set_ids:
        existing_sets = set(db.scalars(
            select(ExamSet.id).where(
                ExamSet.exam_id == exam_id,
                ExamSet.id.in_(set_ids),
            )
        ).all())
        if existing_sets != set_ids:
            raise HTTPException(status_code=400, detail="A question references an invalid exam set.")

    keys = [(question.set_id, question.question_number) for question in questions_data]
    if len(keys) != len(set(keys)):
        raise HTTPException(status_code=400, detail="Question numbers must be unique within each set.")

    question_numbers = {number for _, number in keys}
    existing_questions = db.scalars(
        select(Question).where(
            Question.exam_id == exam_id,
            or_(Question.set_id.in_(set_ids), Question.set_id.is_(None))
            if set_ids
            else Question.set_id.is_(None),
            Question.question_number.in_(question_numbers),
        )
    ).all()
    existing_keys = {(question.set_id, question.question_number) for question in existing_questions}
    if existing_keys.intersection(keys):
        raise HTTPException(status_code=409, detail="A question number already exists in this set.")

    incoming_counts: dict[int | None, int] = {}
    for set_id, _ in keys:
        incoming_counts[set_id] = incoming_counts.get(set_id, 0) + 1
    for set_id, incoming_count in incoming_counts.items():
        existing_count = db.scalar(
            select(func.count(Question.id)).where(
                Question.exam_id == exam_id,
                Question.set_id == set_id if set_id is not None else Question.set_id.is_(None),
            )
        ) or 0
        if existing_count + incoming_count > 2000:
            raise HTTPException(
                status_code=413,
                detail="An exam set cannot exceed 2,000 questions with the current exam delivery design.",
            )

    question_rows = []
    for item in questions_data:
        question = Question(
            exam_id=exam_id,
            question_number=item.question_number,
            question_type=item.question_type,
            question_text=item.question_text,
            image_url=item.image_url,
            audio_url=item.audio_url,
            marks=item.marks,
            created_by=current_admin.id,
            set_id=item.set_id,
            status=item.status or "DRAFT",
        )
        question_rows.append(question)

    try:
        db.add_all(question_rows)
        db.flush()
        option_rows = [
            Option(
                question_id=question.id,
                option_label=option.option_label,
                option_text=option.option_text,
                image_url=option.image_url,
                audio_url=option.audio_url,
                is_correct=option.is_correct,
                image_id=option.image_id,
            )
            for item, question in zip(questions_data, question_rows)
            for option in item.options
        ]
        db.add_all(option_rows)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "message": "Questions created successfully.",
        "created_count": len(question_rows),
        "question_ids": [question.id for question in question_rows],
    }


# =========================
# UPDATE QUESTION
# =========================

@router.put("/questions/{question_id}")
def update_question(
    question_id: int,
    question_data: QuestionUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
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

        destination_set_id = update_data["set_id"]
        if destination_set_id != question.set_id:
            destination_count = db.scalar(
                select(func.count(Question.id)).where(
                    Question.exam_id == question.exam_id,
                    Question.set_id == destination_set_id
                    if destination_set_id is not None
                    else Question.set_id.is_(None),
                )
            ) or 0
            if destination_count >= 2000:
                raise HTTPException(status_code=413, detail="An exam set cannot exceed 2,000 questions.")

    if "question_number" in update_data:
        existing_question = db.scalar(
            select(Question).where(
                Question.exam_id == question.exam_id,
                Question.set_id == update_data.get("set_id", question.set_id),
                Question.question_number
                == update_data["question_number"],
                Question.id != question_id,
            )
        )

        if existing_question is not None:
            raise HTTPException(
                status_code=400,
                detail="Question number already exists in this set.",
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
    current_admin: User = Depends(get_current_admin),
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
