from typing import Optional

from backend.quiz_engine.attempt import Attempt
from backend.quiz_engine.exam import Exam


# ─────────────────────────────────────────
# EXAM REPOSITORY
# ─────────────────────────────────────────

class InMemoryExamRepository:
    def __init__(self) -> None:
        self._exams: dict[str, Exam] = {}

    def save(self, exam: Exam) -> None:
        self._exams[exam.id] = exam

    def get(self, exam_id: str) -> Optional[Exam]:
        return self._exams.get(exam_id)

    def list_all(self) -> list[Exam]:
        return list(self._exams.values())


# ─────────────────────────────────────────
# ATTEMPT REPOSITORY
# ─────────────────────────────────────────

class InMemoryAttemptRepository:
    def __init__(self) -> None:
        self._attempts: dict[str, Attempt] = {}

    def save(self, attempt: Attempt) -> None:
        self._attempts[attempt.id] = attempt

    def get(self, attempt_id: str) -> Optional[Attempt]:
        return self._attempts.get(attempt_id)

    def get_by_exam_and_student(
        self,
        exam_id: str,
        student_id: str,
    ) -> Optional[Attempt]:
        return next(
            (
                attempt
                for attempt in self._attempts.values()
                if attempt.exam_id == exam_id
                and attempt.student_id == student_id
            ),
            None,
        )

    def list_by_student(self, student_id: str) -> list[Attempt]:
        return [
            attempt
            for attempt in self._attempts.values()
            if attempt.student_id == student_id
        ]


# ─────────────────────────────────────────
# AUDIO PLAY TRACKER
# ─────────────────────────────────────────

class InMemoryAudioTracker:
    MAX_PLAYS: int = 2

    def __init__(self) -> None:
        # key: (attempt_id, question_id) → play count
        self._plays: dict[tuple[str, str], int] = {}

    def get_plays(self, attempt_id: str, question_id: str) -> int:
        return self._plays.get((attempt_id, question_id), 0)

    def record_play(self, attempt_id: str, question_id: str) -> int:
        key = (attempt_id, question_id)
        current = self._plays.get(key, 0)

        if current >= self.MAX_PLAYS:
            raise ValueError(
                f"Maximum audio plays ({self.MAX_PLAYS}) reached "
                f"for question {question_id}."
            )

        self._plays[key] = current + 1
        return self._plays[key]

    def plays_remaining(self, attempt_id: str, question_id: str) -> int:
        return self.MAX_PLAYS - self.get_plays(attempt_id, question_id)

    def can_play(self, attempt_id: str, question_id: str) -> bool:
        return self.get_plays(attempt_id, question_id) < self.MAX_PLAYS