from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.orm import (
    ExamModel,
    ExamSetModel,
    OptionModel,
    QuestionModel,
)
from app.repository import postgres


def test_repository_returns_only_questions_from_requested_exam_set(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'set-isolation.db'}")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)

    with session_factory() as session:
        session.add(
            ExamModel(
                id=21,
                title="Isolation test exam",
                duration_minutes=30,
                total_questions=2,
                total_marks=Decimal("5.0"),
                status="PUBLISHED",
                sets=[
                    ExamSetModel(id=171, exam_id=21, set_number=1, set_name="Set 171"),
                    ExamSetModel(id=172, exam_id=21, set_number=2, set_name="Set 172"),
                ],
                questions=[
                    QuestionModel(
                        id=1001,
                        exam_id=21,
                        set_id=171,
                        question_number=1,
                        question_type="READING",
                        question_text="Set 171 only",
                        marks=Decimal("2.5"),
                        status="PUBLISHED",
                        options=[
                            OptionModel(
                                id=10010,
                                question_id=1001,
                                option_label="A",
                                option_text="Option A",
                                is_correct=False,
                            )
                        ],
                    ),
                    QuestionModel(
                        id=1002,
                        exam_id=21,
                        set_id=172,
                        # SQLite does not apply PostgreSQL's partial-index
                        # predicate when creating the model metadata.
                        question_number=2,
                        question_type="READING",
                        question_text="Set 172 only",
                        marks=Decimal("2.5"),
                        status="PUBLISHED",
                        options=[
                            OptionModel(
                                id=10020,
                                question_id=1002,
                                option_label="A",
                                option_text="Option A",
                                is_correct=False,
                            )
                        ],
                    ),
                ],
            )
        )
        session.commit()

    monkeypatch.setattr(
        postgres,
        "SessionLocal",
        lambda: session_factory(),
    )
    try:
        repository = postgres.PostgresExamRepository()
        first_set = repository.get("21", "171")
        second_set = repository.get("21", "172")

        assert [question.text for question in first_set.questions] == ["Set 171 only"]
        assert [question.text for question in second_set.questions] == ["Set 172 only"]
        assert first_set.questions[0].id == "1001"
        assert second_set.questions[0].id == "1002"
        assert first_set.questions[0].options[0].id == "10010"
        assert second_set.questions[0].options[0].id == "10020"
    finally:
        engine.dispose()
