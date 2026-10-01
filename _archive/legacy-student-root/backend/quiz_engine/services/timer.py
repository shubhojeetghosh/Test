from datetime import datetime, timezone

from backend.quiz_engine.attempt import Attempt, AttemptStatus


class QuizTimer:
    @staticmethod
    def remaining_seconds(attempt: Attempt) -> int:
        if attempt.expires_at is None:
            raise ValueError("Attempt has not been started.")

        remaining = int(
            attempt.expires_at
            - datetime.now(timezone.utc).timestamp()
        )

        return max(0, remaining)

    @staticmethod
    def is_expired(attempt: Attempt) -> bool:
        if attempt.expires_at is None:
            return False

        expired = (
            datetime.now(timezone.utc).timestamp()
            >= attempt.expires_at
        )

        if expired and attempt.status == AttemptStatus.IN_PROGRESS:
            attempt.status = AttemptStatus.EXPIRED

        return expired

    @staticmethod
    def expire_if_needed(attempt: Attempt) -> None:
        if QuizTimer.is_expired(attempt):
            raise ValueError("Attempt has expired.")