from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repository.database_exam import DatabaseExamRepository


router = APIRouter(
    prefix="/student/exams",
    tags=["Student Exams"],
)


@router.get("/{exam_id}")
def get_student_exam(
    exam_id: str,
    db: Session = Depends(get_db),
):
    repository = DatabaseExamRepository(db)

    try:
        exam = repository.get_exam(exam_id)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    if exam is None:
        raise HTTPException(
            status_code=404,
            detail="Exam not found",
        )

    return {
        "id": exam.id,
        "title": exam.title,
        "duration_minutes": exam.duration_minutes,
        "total_questions": exam.total_questions,
        "marks_per_question": exam.marks_per_question,
        "total_marks": exam.total_marks,
        "questions": [
            {
                "id": question.id,
                "question_number": question.question_number,
                "question_type": question.question_type.value,
                "text": question.text,
                "image_url": question.image_url,
                "audio_url": question.audio_url,
                "options": [
                    {
                        "id": option.id,
                        "text": option.text,
                        "audio_url": option.audio_url,
                    }
                    for option in question.options
                ],
            }
            for question in exam.questions
        ],
    }