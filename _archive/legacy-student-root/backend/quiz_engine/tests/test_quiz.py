import pytest

from backend.quiz_engine.attempt import Attempt, AttemptStatus
from backend.quiz_engine.exam import Exam
from backend.quiz_engine.question import Option, Question, QuestionType
from backend.quiz_engine.quiz import QuizEngine


def make_question(number: int) -> Question:
    return Question(
        id=f"q{number}",
        question_number=number,
        question_type=QuestionType.READING,
        text=f"Question {number}",
        options=[
            Option(id=f"{number}a", text="Wrong"),
            Option(id=f"{number}b", text="Correct", is_correct=True),
        ],
    )


def make_exam() -> Exam:
    exam = Exam(
        id="exam1",
        title="EPS-TOPIK Practice",
    )

    for number in range(1, 41):
        exam.add_question(make_question(number))

    return exam


def make_attempt() -> Attempt:
    return Attempt(
        id="attempt1",
        student_id="student1",
        exam_id="exam1",
    )


def test_engine_starts_attempt():
    exam = make_exam()
    engine = QuizEngine(exam)
    attempt = make_attempt()

    engine.start_attempt(attempt)

    assert attempt.status == AttemptStatus.IN_PROGRESS


def test_engine_gets_question():
    exam = make_exam()
    engine = QuizEngine(exam)

    question = engine.get_question(10)

    assert question.id == "q10"
    assert question.question_number == 10


def test_engine_rejects_invalid_question_number():
    exam = make_exam()
    engine = QuizEngine(exam)

    with pytest.raises(ValueError):
        engine.get_question(41)


def test_engine_answers_question():
    exam = make_exam()
    engine = QuizEngine(exam)
    attempt = make_attempt()

    engine.start_attempt(attempt)
    engine.answer_question(attempt, "q1", "1b")

    assert attempt.answers["q1"].selected_option_id == "1b"


def test_engine_rejects_invalid_option():
    exam = make_exam()
    engine = QuizEngine(exam)
    attempt = make_attempt()

    engine.start_attempt(attempt)

    with pytest.raises(ValueError):
        engine.answer_question(attempt, "q1", "invalid")


def test_question_navigation():
    exam = make_exam()
    engine = QuizEngine(exam)
    attempt = make_attempt()

    assert attempt.current_question == 1

    engine.next_question(attempt)
    assert attempt.current_question == 2

    engine.previous_question(attempt)
    assert attempt.current_question == 1


def test_navigation_does_not_go_below_one():
    exam = make_exam()
    engine = QuizEngine(exam)
    attempt = make_attempt()

    engine.previous_question(attempt)

    assert attempt.current_question == 1


def test_navigation_does_not_go_above_forty():
    exam = make_exam()
    engine = QuizEngine(exam)
    attempt = make_attempt()

    attempt.current_question = 40
    engine.next_question(attempt)

    assert attempt.current_question == 40


def test_engine_submits_attempt():
    exam = make_exam()
    engine = QuizEngine(exam)
    attempt = make_attempt()

    engine.start_attempt(attempt)
    engine.submit_attempt(attempt)

    assert attempt.status == AttemptStatus.SUBMITTED


def test_engine_rejects_attempt_for_different_exam():
    exam = make_exam()
    engine = QuizEngine(exam)

    wrong_attempt = Attempt(
        id="attempt_wrong",
        student_id="student1",
        exam_id="different_exam",
    )

    with pytest.raises(ValueError):
        engine.start_attempt(wrong_attempt)


def test_duplicate_answer_submission_updates_previous_answer():
    exam = make_exam()
    engine = QuizEngine(exam)
    attempt = make_attempt()

    engine.start_attempt(attempt)
    engine.answer_question(attempt, "q1", "1a")
    engine.answer_question(attempt, "q1", "1b")

    assert attempt.answers["q1"].selected_option_id == "1b"
    assert len(attempt.answers) == 1


def test_engine_rejects_answer_for_unknown_question():
    exam = make_exam()
    engine = QuizEngine(exam)
    attempt = make_attempt()

    engine.start_attempt(attempt)

    with pytest.raises(ValueError):
        engine.answer_question(attempt, "q999", "1a")