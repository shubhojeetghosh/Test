from datetime import datetime, timezone
from collections import OrderedDict
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session, selectinload

from app.models.attempt import Answer, Attempt, AttemptStatus
from app.core.database import SessionLocal
from app.models.exam import Exam
from app.models.orm import (
    ExamModel,
    ExamSessionModel,
    OptionModel,
    QuestionModel,
    StudentAnswerModel,
    AudioPlayLogModel,
)
from app.models.question import Option, Question, QuestionType


# ── helpers ───────────────────────────────────────────────────────────────────

def _qtype(raw: str) -> QuestionType:
    """Map DB question_type string → QuestionType enum."""
    mapping = {
        "READING":      QuestionType.READING,
        "IMAGE":        QuestionType.IMAGE,
        "IMAGE_AUDIO":  QuestionType.IMAGE_AUDIO,
        "AUDIO_OPTION": QuestionType.AUDIO_OPTION,
    }
    return mapping.get(raw.upper(), QuestionType.READING)


def _build_option(row: OptionModel) -> Option:
    return Option(
        id=str(row.id),
        text=row.option_text or "",
        is_correct=row.is_correct,
        audio_url=row.audio_url,
    )

def _build_question(row: QuestionModel) -> Question:
    return Question(
        id=str(row.id),
        question_number=row.question_number,
        question_type=_qtype(row.question_type),
        text=row.question_text or "",
        marks=float(row.marks),
        image_url=row.image_url,
        audio_url=row.audio_url,
        options=[_build_option(o) for o in row.options],
    )


def _build_exam(row: ExamModel) -> Exam:
    exam = Exam(
        id=str(row.id),
        title=row.title,
        duration_minutes=row.duration_minutes,
        total_questions=row.total_questions,
        marks_per_question=(
            float(row.total_marks) / row.total_questions
            if row.total_questions
            else 0.0
        ),
    )
    for q_row in row.questions:
        exam.add_question(_build_question(q_row))
    return exam


# ─────────────────────────────────────────────────────────────────────────────
# EXAM REPOSITORY
# ─────────────────────────────────────────────────────────────────────────────

class PostgresExamRepository:
    """
    Reads exams + questions + options from the database.
    Exams are loaded on demand and cached per process. Loading one exam at a
    time avoids a cold start reading every exam and question in the database.
    """

    def __init__(self) -> None:
        self._cache: OrderedDict[str, Exam] = OrderedDict()
        self._max_cached_exams = 16

    def save(self, exam: Exam) -> None:
        """For compatibility with in-memory interface — updates the cache."""
        self._cache[exam.id] = exam
        self._cache.move_to_end(exam.id)
        while len(self._cache) > self._max_cached_exams:
            self._cache.popitem(last=False)

    def get(self, exam_id: str) -> Optional[Exam]:
        cached = self._cache.get(str(exam_id))
        if cached is not None:
            self._cache.move_to_end(str(exam_id))
            return cached

        try:
            db_exam_id = int(exam_id)
        except (TypeError, ValueError):
            return None

        db: Session = SessionLocal()
        try:
            row = (
                db.query(ExamModel)
                .options(
                    selectinload(ExamModel.questions).selectinload(
                        QuestionModel.options
                    )
                )
                .filter(ExamModel.id == db_exam_id)
                .first()
            )
            if row is None:
                return None
            exam = _build_exam(row)
            self.save(exam)
            return exam
        finally:
            db.close()

    def list_all(self) -> list[Exam]:
        db: Session = SessionLocal()
        try:
            exam_ids = [row[0] for row in db.query(ExamModel.id).order_by(ExamModel.id).all()]
        finally:
            db.close()
        return [exam for exam_id in exam_ids if (exam := self.get(str(exam_id))) is not None]


# ─────────────────────────────────────────────────────────────────────────────
# ATTEMPT REPOSITORY
# ─────────────────────────────────────────────────────────────────────────────

class PostgresAttemptRepository:
    """
    Persists attempts and answers in PostgreSQL. Attempt IDs are derived from
    the database primary key so any serverless instance can reload the record.
    """

    def __init__(self) -> None:
        # State is in PostgreSQL; this repository intentionally has no cache.
        pass

    @staticmethod
    def _db_id(attempt_id: str) -> Optional[int]:
        prefix, separator, value = str(attempt_id).partition("_")
        if prefix != "attempt" or not separator or not value.isdecimal():
            return None
        return int(value)

    @staticmethod
    def _as_utc(value: Optional[datetime]) -> Optional[datetime]:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    # ── private helpers ───────────────────────────────────────────────────────

    def _session_to_attempt(self, row: ExamSessionModel) -> Attempt:
        """Convert a DB ExamSessionModel row → Attempt domain object."""
        str_id = f"attempt_{row.id}"
        attempt = Attempt(
            id=str_id,
            student_id=str(row.user_id),
            exam_id=str(row.exam_id),
            started_at=self._as_utc(row.started_at),
            expires_at=(
                self._as_utc(row.started_at).timestamp()
                + int(row.exam.duration_minutes) * 60
            ) if row.started_at else None,
            status=self._map_status(row.status),
            current_question=1,
        )
        # restore answers
        for ans_row in row.answers:
            if ans_row.selected_option_id is not None:
                answer = Answer(
                    question_id=str(ans_row.question_id),
                    selected_option_id=str(ans_row.selected_option_id),
                    answered_at=self._as_utc(ans_row.answered_at),
                )
                attempt.answers[answer.question_id] = answer
        return attempt

    @staticmethod
    def _map_status(db_status: str) -> AttemptStatus:
        mapping = {
            "IN_PROGRESS":    AttemptStatus.IN_PROGRESS,
            "SUBMITTED":      AttemptStatus.SUBMITTED,
            "AUTO_SUBMITTED": AttemptStatus.EXPIRED,
        }
        return mapping.get(db_status, AttemptStatus.IN_PROGRESS)

    @staticmethod
    def _domain_status(status: AttemptStatus) -> str:
        mapping = {
            AttemptStatus.IN_PROGRESS: "IN_PROGRESS",
            AttemptStatus.SUBMITTED:   "SUBMITTED",
            AttemptStatus.EXPIRED:     "AUTO_SUBMITTED",
            AttemptStatus.NOT_STARTED: "IN_PROGRESS",
        }
        return mapping.get(status, "IN_PROGRESS")

    # ── public interface ──────────────────────────────────────────────────────

    def save(self, attempt: Attempt) -> None:
        """
        Upsert the attempt to exam_sessions and sync all answers
        to student_answers.
        """
        db: Session = SessionLocal()
        try:
            db_id = self._db_id(attempt.id)
            if db_id is None:
                try:
                    user_id = int(attempt.student_id)
                    exam_id = int(attempt.exam_id)
                except (ValueError, TypeError) as exc:
                    raise ValueError("Attempt must reference persisted user and exam IDs.") from exc
                session_row = ExamSessionModel(
                    user_id=user_id,
                    exam_id=exam_id,
                    started_at=attempt.started_at or datetime.now(timezone.utc),
                    status=self._domain_status(attempt.status),
                )
                db.add(session_row)
                db.flush()
                db_id = session_row.id
                attempt.id = f"attempt_{db_id}"
            else:
                session_row = (
                    db.query(ExamSessionModel)
                    .filter_by(id=db_id)
                    .with_for_update()
                    .first()
                )
                if session_row is None:
                    raise ValueError("Attempt no longer exists.")

                if (
                    session_row.status in ("SUBMITTED", "AUTO_SUBMITTED")
                    and attempt.status == AttemptStatus.IN_PROGRESS
                ):
                    raise ValueError("Attempt is no longer active.")

            session_row.status = self._domain_status(attempt.status)
            if attempt.status in (AttemptStatus.SUBMITTED, AttemptStatus.EXPIRED):
                session_row.submitted_at = session_row.submitted_at or datetime.now(timezone.utc)

            # Fetch existing answers in one query instead of one query per item.
            answer_values = []
            for question_str_id, answer in attempt.answers.items():
                if answer.selected_option_id is None:
                    continue
                try:
                    answer_values.append((
                        int(question_str_id),
                        int(answer.selected_option_id),
                        answer.answered_at or datetime.now(timezone.utc),
                    ))
                except (ValueError, TypeError):
                    continue

            question_ids = [value[0] for value in answer_values]
            existing_answers = {}
            if question_ids:
                existing_answers = {
                    row.question_id: row
                    for row in db.query(StudentAnswerModel)
                    .filter(
                        StudentAnswerModel.attempt_id == db_id,
                        StudentAnswerModel.question_id.in_(question_ids),
                    )
                    .all()
                }

            for question_id, option_id, answered_at in answer_values:
                existing = existing_answers.get(question_id)
                if existing is None:
                    db.add(StudentAnswerModel(
                        attempt_id=db_id,
                        question_id=question_id,
                        selected_option_id=option_id,
                        answered_at=answered_at,
                    ))
                else:
                    existing.selected_option_id = option_id
                    existing.answered_at = answered_at

            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def get(self, attempt_id: str) -> Optional[Attempt]:
        db_id = self._db_id(attempt_id)
        if db_id is None:
            return None

        db: Session = SessionLocal()
        try:
            row = (
                db.query(ExamSessionModel)
                .options(
                    selectinload(ExamSessionModel.exam),
                    selectinload(ExamSessionModel.answers),
                )
                .filter_by(id=db_id)
                .first()
            )
            if row is None:
                return None
            return self._session_to_attempt(row)
        finally:
            db.close()

    def get_by_exam_and_student(
        self, exam_id: str, student_id: str
    ) -> Optional[Attempt]:
        try:
            db_exam_id = int(exam_id)
        except ValueError:
            return None

        try:
            db_user_id = int(student_id)
        except ValueError:
            return None

        db: Session = SessionLocal()
        try:
            row = (
                db.query(ExamSessionModel)
                .options(
                    selectinload(ExamSessionModel.exam),
                    selectinload(ExamSessionModel.answers),
                )
                .filter_by(exam_id=db_exam_id, user_id=db_user_id)
                .order_by(ExamSessionModel.id.desc())
                .first()
            )

            if row is None:
                return None

            return self._session_to_attempt(row)
        finally:
            db.close()

    def start_or_resume(self, attempt: Attempt) -> Attempt:
        """Atomically resume or create an attempt across all app instances."""
        try:
            exam_id = int(attempt.exam_id)
            user_id = int(attempt.student_id)
        except (TypeError, ValueError) as exc:
            raise ValueError("Attempt must reference persisted user and exam IDs.") from exc

        db: Session = SessionLocal()
        try:
            # Transaction-scoped lock serializes simultaneous starts for this
            # user/exam pair, including requests sent to different instances.
            if db.get_bind().dialect.name == "postgresql":
                db.execute(
                    text("SELECT pg_advisory_xact_lock(:user_id, :exam_id)"),
                    {"user_id": user_id, "exam_id": exam_id},
                )

            submitted = (
                db.query(ExamSessionModel)
                .options(
                    selectinload(ExamSessionModel.exam),
                    selectinload(ExamSessionModel.answers),
                )
                .filter_by(
                    exam_id=exam_id,
                    user_id=user_id,
                    status="SUBMITTED",
                )
                .order_by(ExamSessionModel.id.desc())
                .with_for_update()
                .first()
            )
            if submitted is not None:
                db.commit()
                return self._session_to_attempt(submitted)

            existing = (
                db.query(ExamSessionModel)
                .options(
                    selectinload(ExamSessionModel.exam),
                    selectinload(ExamSessionModel.answers),
                )
                .filter_by(exam_id=exam_id, user_id=user_id)
                .order_by(ExamSessionModel.id.desc())
                .with_for_update()
                .first()
            )
            if existing is not None:
                current = self._session_to_attempt(existing)
                if current.status == AttemptStatus.IN_PROGRESS:
                    if not current.is_expired():
                        db.commit()
                        return current
                    existing.status = "AUTO_SUBMITTED"
                    existing.submitted_at = existing.submitted_at or datetime.now(timezone.utc)
                elif current.status == AttemptStatus.SUBMITTED:
                    db.commit()
                    return current

            row = ExamSessionModel(
                user_id=user_id,
                exam_id=exam_id,
                started_at=attempt.started_at or datetime.now(timezone.utc),
                status="IN_PROGRESS",
            )
            db.add(row)
            db.flush()
            attempt.id = f"attempt_{row.id}"
            db.commit()
            return attempt
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def list_by_student(self, student_id: str) -> list[Attempt]:
        try:
            db_user_id = int(student_id)
        except ValueError:
            return []

        db: Session = SessionLocal()
        try:
            rows = (
                db.query(ExamSessionModel)
                .options(
                    selectinload(ExamSessionModel.exam),
                    selectinload(ExamSessionModel.answers),
                )
                .filter_by(user_id=db_user_id)
                .order_by(ExamSessionModel.id.desc())
                .all()
            )
            result = []
            for row in rows:
                str_id = f"attempt_{row.id}"
                attempt = self._session_to_attempt(row)
                attempt.id = str_id
                result.append(attempt)
            return result
        finally:
            db.close()


# ─────────────────────────────────────────────────────────────────────────────
# AUDIO TRACKER
# ─────────────────────────────────────────────────────────────────────────────

class PostgresAudioTracker:
    """
    Persists audio play counts to PostgreSQL. The attempt row is locked while
    incrementing so simultaneous requests cannot bypass the play limit.
    """

    MAX_PLAYS: int = 2

    def __init__(self) -> None:
        pass

    def _db_ids(
        self, attempt_id: str, question_id: str, db: Session
    ) -> tuple[Optional[int], Optional[int]]:
        """Resolve string attempt/question IDs to integer DB ids."""
        db_attempt_id = PostgresAttemptRepository._db_id(attempt_id)
        if db_attempt_id is None:
            return None, None
        try:
            db_question_id = int(question_id)
        except ValueError:
            return None, None
        return db_attempt_id, db_question_id

    def get_plays(self, attempt_id: str, question_id: str) -> int:
        db: Session = SessionLocal()
        try:
            db_attempt_id, db_question_id = self._db_ids(attempt_id, question_id, db)
            if db_attempt_id is None:
                return 0
            row = db.query(AudioPlayLogModel).filter_by(
                attempt_id=db_attempt_id,
                question_id=db_question_id,
            ).first()
            return row.play_count if row else 0
        finally:
            db.close()

    def record_play(self, attempt_id: str, question_id: str) -> int:
        db: Session = SessionLocal()
        try:
            db_attempt_id, db_question_id = self._db_ids(attempt_id, question_id, db)
            if db_attempt_id is None:
                raise ValueError("Invalid attempt or question ID.")

            # Serialize play-count changes per attempt, including serverless
            # requests routed to separate function instances.
            session_row = (
                db.query(ExamSessionModel)
                .filter_by(id=db_attempt_id)
                .with_for_update()
                .first()
            )
            if session_row is None:
                raise ValueError("Attempt not found.")

            row = (
                db.query(AudioPlayLogModel)
                .filter_by(
                    attempt_id=db_attempt_id,
                    question_id=db_question_id,
                )
                .with_for_update()
                .first()
            )
            current = row.play_count if row else 0
            if current >= self.MAX_PLAYS:
                raise ValueError(
                    f"Maximum audio plays ({self.MAX_PLAYS}) reached "
                    f"for question {question_id}."
                )

            new_count = current + 1
            if row is None:
                db.add(AudioPlayLogModel(
                    attempt_id=db_attempt_id,
                    question_id=db_question_id,
                    play_count=new_count,
                ))
            else:
                row.play_count = new_count

            db.commit()
            return new_count
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def plays_remaining(self, attempt_id: str, question_id: str) -> int:
        return self.MAX_PLAYS - self.get_plays(attempt_id, question_id)

    def can_play(self, attempt_id: str, question_id: str) -> bool:
        return self.get_plays(attempt_id, question_id) < self.MAX_PLAYS
