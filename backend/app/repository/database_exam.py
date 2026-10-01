from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.admin_portal.models.exam import Exam as ExamORM
from app.admin_portal.models.question import Question as QuestionORM
from app.admin_portal.models.option import Option as OptionORM

from app.models.exam import Exam
from app.models.question import Option, Question, QuestionType


class DatabaseExamRepository:
    """
    Loads exams, questions, and options from PostgreSQL
    and converts them into domain model objects.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_exam(self, exam_id: str) -> Optional[Exam]:
        """
        Load one exam and its questions and options.

        Args:
            exam_id: Database exam ID as a string.

        Returns:
            A domain Exam object if found, otherwise None.
        """

        # 1. Load the exam record.
        db_exam = self.db.execute(
            select(ExamORM).where(
                ExamORM.id == int(exam_id)
            )
        ).scalar_one_or_none()

        if db_exam is None:
            return None

        # 2. Load all questions belonging to this exam.
        db_questions = self.db.execute(
            select(QuestionORM)
            .where(QuestionORM.exam_id == db_exam.id)
            .order_by(QuestionORM.question_number)
        ).scalars().all()

        # 3. Convert the database exam into the domain Exam model.
        exam = Exam(
            id=str(db_exam.id),
            title=db_exam.title,
            duration_minutes=db_exam.duration_minutes,
            total_questions=db_exam.total_questions,
            marks_per_question=(
                float(db_exam.total_marks) / db_exam.total_questions
                if db_exam.total_questions > 0
                else 0.0
            ),
        )

        # 4. Convert every database question.
        for db_question in db_questions:

            # 5. Load options belonging to this question.
            db_options = self.db.execute(
                select(OptionORM)
                .where(
                    OptionORM.question_id == db_question.id
                )
                .order_by(OptionORM.id)
            ).scalars().all()

            # 6. Convert database options into domain Option objects.
            options = [
                Option(
                    id=str(db_option.id),
                    text=db_option.option_text or "",
                    is_correct=db_option.is_correct,
                    audio_url=db_option.audio_url,
                )
                for db_option in db_options
            ]

            # 7. Convert the database question into the domain Question model.
            question = Question(
                id=str(db_question.id),
                question_number=db_question.question_number,
                question_type=QuestionType(
                    db_question.question_type.lower()
                ),
                text=db_question.question_text or "",
                marks=float(db_question.marks),
                image_url=db_question.image_url,
                audio_url=db_question.audio_url,
                options=options,
            )

            # 8. Add the question to the exam.
            exam.add_question(question)

        return exam

def list_all(self) -> list[Exam]:
    """
    Returns all exams from Supabase.

    Only exam metadata is loaded here. Questions and options
    are loaded when a specific exam is requested.
    """

    db_exams = self.db.execute(
        select(ExamORM).order_by(ExamORM.id)
    ).scalars().all()

    exams: list[Exam] = []

    for db_exam in db_exams:
        marks_per_question = (
            float(db_exam.total_marks) / db_exam.total_questions
            if db_exam.total_questions > 0
            else 0.0
        )

        exams.append(
            Exam(
                id=str(db_exam.id),
                title=db_exam.title,
                duration_minutes=db_exam.duration_minutes,
                total_questions=db_exam.total_questions,
                marks_per_question=marks_per_question,
            )
        )

    return exams