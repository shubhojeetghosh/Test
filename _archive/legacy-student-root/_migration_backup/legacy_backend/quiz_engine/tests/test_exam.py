import pytest

from backend.quiz_engine.exam import Exam
from backend.quiz_engine.question import Option, Question, QuestionType


def make_question(number: int) -> Question:
    return Question(
        id=f"q{number}",
        question_number=number,
        question_type=QuestionType.READING,
        text=f"Question {number}",
        options=[
            Option(id=f"q{number}a", text="Wrong"),
            Option(id=f"q{number}b", text="Correct", is_correct=True),
        ],
    )


def test_exam_has_correct_defaults():
    exam = Exam(
        id="exam1",
        title="EPS-TOPIK Practice",
    )

    assert exam.duration_minutes == 50
    assert exam.total_questions == 40
    assert exam.marks_per_question == 2.5
    assert exam.total_marks == 100.0


def test_exam_accepts_40_questions():
    exam = Exam(
        id="exam1",
        title="EPS-TOPIK Practice",
    )

    for number in range(1, 41):
        exam.add_question(make_question(number))

    exam.validate()

    assert len(exam.questions) == 40


def test_exam_rejects_41st_question():
    exam = Exam(
        id="exam1",
        title="EPS-TOPIK Practice",
    )

    for number in range(1, 41):
        exam.add_question(make_question(number))

    with pytest.raises(ValueError):
        exam.add_question(make_question(41))


def test_exam_rejects_incomplete_exam():
    exam = Exam(
        id="exam1",
        title="EPS-TOPIK Practice",
    )

    exam.add_question(make_question(1))

    with pytest.raises(ValueError):
        exam.validate()
        