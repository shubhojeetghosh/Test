from backend.quiz_engine.attempt import Attempt, AttemptStatus
from backend.quiz_engine.services.timer import QuizTimer


def make_attempt() -> Attempt:
    return Attempt(
        id="attempt1",
        student_id="student1",
        exam_id="exam1",
    )


def test_timer_starts_with_attempt():
    attempt = make_attempt()
    attempt.start(50)

    remaining = QuizTimer.remaining_seconds(attempt)

    assert remaining > 0
    assert remaining <= 3000


def test_active_attempt_is_not_expired():
    attempt = make_attempt()
    attempt.start(50)

    assert QuizTimer.is_expired(attempt) is False
    assert attempt.status == AttemptStatus.IN_PROGRESS


def test_expired_attempt_changes_status():
    attempt = make_attempt()
    attempt.start(50)

    attempt.expires_at = 0

    assert QuizTimer.is_expired(attempt) is True
    assert attempt.status == AttemptStatus.EXPIRED