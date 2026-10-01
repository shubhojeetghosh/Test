import pytest

from backend.quiz_engine.question import Option, Question, QuestionType


def test_question_can_be_created():
    question = Question(
        id="q1",
        question_number=1,
        question_type=QuestionType.READING,
        text="What is 1 + 1?",
        options=[
            Option(id="a", text="1"),
            Option(id="b", text="2", is_correct=True),
        ],
    )

    assert question.id == "q1"
    assert question.marks == 2.5
    assert question.is_correct("b") is True


def test_invalid_option_is_rejected():
    question = Question(
        id="q1",
        question_number=1,
        question_type=QuestionType.READING,
        text="Question",
        options=[Option(id="a", text="A")],
    )

    with pytest.raises(ValueError):
        question.is_correct("invalid")