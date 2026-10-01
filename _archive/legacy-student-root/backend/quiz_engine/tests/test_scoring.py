from backend.quiz_engine.attempt import Attempt
from backend.quiz_engine.exam import Exam
from backend.quiz_engine.question import Option, Question, QuestionType
from backend.quiz_engine.services.scoring import QuizScorer


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
        title="Test Exam",
        total_questions=2,
    )

    exam.add_question(make_question(1))
    exam.add_question(make_question(2))

    return exam


def make_attempt() -> Attempt:
    attempt = Attempt(
        id="attempt1",
        student_id="student1",
        exam_id="exam1",
    )

    attempt.start(50)

    return attempt


def test_correct_answer_gets_marks():
    exam = make_exam()
    attempt = make_attempt()

    attempt.save_answer("q1", "1b")

    scorer = QuizScorer(exam)

    assert scorer.calculate_score(attempt) == 2.5


def test_wrong_answer_gets_zero():
    exam = make_exam()
    attempt = make_attempt()

    attempt.save_answer("q1", "1a")

    scorer = QuizScorer(exam)

    assert scorer.calculate_score(attempt) == 0.0


def test_multiple_correct_answers_are_scored():
    exam = make_exam()
    attempt = make_attempt()

    attempt.save_answer("q1", "1b")
    attempt.save_answer("q2", "2b")

    scorer = QuizScorer(exam)

    assert scorer.calculate_score(attempt) == 5.0


def test_percentage_is_calculated():
    exam = make_exam()
    attempt = make_attempt()

    attempt.save_answer("q1", "1b")

    scorer = QuizScorer(exam)

    assert scorer.calculate_percentage(attempt) == 50.0