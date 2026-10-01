from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class AttemptStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    EXPIRED = "expired"


@dataclass
class Answer:
    question_id: str
    selected_option_id: Optional[str] = None
    answered_at: Optional[datetime] = None

    def select(self, option_id: str) -> None:
        self.selected_option_id = option_id
        self.answered_at = datetime.now(timezone.utc)


@dataclass
class Attempt:
    id: str
    student_id: str
    exam_id: str
    started_at: Optional[datetime] = None
    expires_at: Optional[float] = None
    status: AttemptStatus = AttemptStatus.NOT_STARTED
    current_question: int = 1
    answers: dict[str, Answer] = field(default_factory=dict)

    def start(self, duration_minutes: int) -> None:
        if self.status != AttemptStatus.NOT_STARTED:
            raise ValueError("Attempt has already been started.")

        now = datetime.now(timezone.utc)

        self.started_at = now
        self.expires_at = now.timestamp() + duration_minutes * 60
        self.status = AttemptStatus.IN_PROGRESS

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False

        return datetime.now(timezone.utc).timestamp() >= self.expires_at

    def save_answer(self, question_id: str, option_id: str) -> None:
        if self.status != AttemptStatus.IN_PROGRESS:
            raise ValueError("Attempt is not active.")

        if self.is_expired():
            self.status = AttemptStatus.EXPIRED
            raise ValueError("Attempt has expired.")

        answer = self.answers.setdefault(
            question_id,
            Answer(question_id=question_id),
        )

        answer.select(option_id)

    def submit(self) -> None:
        if self.status != AttemptStatus.IN_PROGRESS:
            raise ValueError("Only an active attempt can be submitted.")

        if self.is_expired():
            self.status = AttemptStatus.EXPIRED
            raise ValueError("Attempt has expired.")

        self.status = AttemptStatus.SUBMITTED