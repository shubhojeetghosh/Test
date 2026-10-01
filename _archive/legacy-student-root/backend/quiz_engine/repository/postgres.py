from backend.quiz_engine.database import SessionLocal
from backend.quiz_engine.models import (
    ExamModel,
    ExamSessionModel,
    OptionModel,
    QuestionModel,
    StudentAnswerModel,
    AudioPlayLogModel,
)

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from backend.quiz_engine.attempt import Answer, Attempt, AttemptStatus
from backend.quiz_engine.database import SessionLocal
from backend.quiz_engine.exam import Exam
from backend.quiz_engine.models import (
    ExamModel,
    ExamSessionModel,
    OptionModel,
    QuestionModel,
    StudentAnswerModel,
    AudioPlayLogModel,
)
from backend.quiz_engine.question import Option, Question, QuestionType


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
        image_url=row.image_url,
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
        marks_per_question=float(row.total_marks) / row.total_questions,
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
    Results are cached in-process for the lifetime of the app instance
    (exams don't change at runtime; cache is invalidated on app restart).
    """

    def __init__(self) -> None:
        self._cache: dict[str, Exam] = {}

    def _load_all(self) -> None:
        """Load all exams from DB into the in-process cache."""
        db: Session = SessionLocal()
        try:
            rows = db.query(ExamModel).all()
            for row in rows:
                exam = _build_exam(row)
                self._cache[exam.id] = exam
        finally:
            db.close()

    def _ensure_loaded(self) -> None:
        if not self._cache:
            self._load_all()

    def save(self, exam: Exam) -> None:
        """For compatibility with in-memory interface — updates the cache."""
        self._cache[exam.id] = exam

    def get(self, exam_id: str) -> Optional[Exam]:
        self._ensure_loaded()
        return self._cache.get(exam_id)

    def list_all(self) -> list[Exam]:
        self._ensure_loaded()
        return list(self._cache.values())


# ─────────────────────────────────────────────────────────────────────────────
# ATTEMPT REPOSITORY
# ─────────────────────────────────────────────────────────────────────────────

class PostgresAttemptRepository:
    """
    Persists exam sessions (attempts), student answers to Neon.
    Also keeps an in-process cache so repeated get() calls within
    a single request don't hit the DB.
    """

    def __init__(self) -> None:
        # string attempt_id → Attempt domain object
        self._cache: dict[str, Attempt] = {}
        # string attempt_id → integer exam_sessions.id
        self._id_map: dict[str, int] = {}

    # ── private helpers ───────────────────────────────────────────────────────

    def _session_to_attempt(self, row: ExamSessionModel) -> Attempt:
        """Convert a DB ExamSessionModel row → Attempt domain object."""
        str_id = f"attempt_{row.id}"
        attempt = Attempt(
            id=str_id,
            student_id=str(row.user_id),
            exam_id=str(row.exam_id),
            started_at=row.started_at.replace(tzinfo=timezone.utc) if row.started_at else None,
            expires_at=(
                row.started_at.replace(tzinfo=timezone.utc).timestamp()
                + 50 * 60          # 50-minute window from started_at
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
                    answered_at=ans_row.answered_at.replace(tzinfo=timezone.utc)
                        if ans_row.answered_at else None,
                )
                attempt.answers[answer.question_id] = answer
        return attempt

    @staticmethod
    def _map_status(db_status: str) -> AttemptStatus:
        mapping = {
            "IN_PROGRESS":    AttemptStatus.IN_PROGRESS,
            "SUBMITTED":      AttemptStatus.SUBMITTED,
            "AUTO_SUBMITTED": AttemptStatus.SUBMITTED,
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
        self._cache[attempt.id] = attempt

        db: Session = SessionLocal()
        try:
            # Determine the integer DB id
            db_id = self._id_map.get(attempt.id)

            if db_id is None:
                # New attempt — create exam_sessions row.
                # user_id: try to cast attempt.student_id to int; default 0
                try:
                    user_id = int(attempt.student_id)
                except (ValueError, TypeError):
                    user_id = 1   # default to first user until auth is integrated

                try:
                    exam_id = int(attempt.exam_id)
                except (ValueError, TypeError):
                    # string like "exam1" — look up by title prefix
                    row = db.query(ExamModel).first()
                    exam_id = row.id if row else 1

                session_row = ExamSessionModel(
                    user_id=user_id,
                    exam_id=exam_id,
                    started_at=attempt.started_at or datetime.now(timezone.utc),
                    status=self._domain_status(attempt.status),
                )
                db.add(session_row)
                db.flush()
                db_id = session_row.id
                self._id_map[attempt.id] = db_id
            else:
                # Existing attempt — update status + submitted_at
                session_row = db.query(ExamSessionModel).filter_by(id=db_id).first()
                if session_row:
                    session_row.status = self._domain_status(attempt.status)
                    if attempt.status == AttemptStatus.SUBMITTED and not session_row.submitted_at:
                        session_row.submitted_at = datetime.now(timezone.utc)

            # Sync answers — upsert each student_answer row
            for question_str_id, answer in attempt.answers.items():
                if answer.selected_option_id is None:
                    continue
                try:
                    q_id = int(question_str_id)
                except ValueError:
                    continue
                try:
                    opt_id = int(answer.selected_option_id)
                except ValueError:
                    continue

                existing_ans = db.query(StudentAnswerModel).filter_by(
                    attempt_id=db_id,
                    question_id=q_id,
                ).first()

                if existing_ans:
                    existing_ans.selected_option_id = opt_id
                    existing_ans.answered_at = answer.answered_at or datetime.now(timezone.utc)
                else:
                    db.add(StudentAnswerModel(
                        attempt_id=db_id,
                        question_id=q_id,
                        selected_option_id=opt_id,
                        answered_at=answer.answered_at or datetime.now(timezone.utc),
                    ))

            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def get(self, attempt_id: str) -> Optional[Attempt]:
        if attempt_id in self._cache:
            return self._cache[attempt_id]

        # Try to load from DB using the id_map
        db_id = self._id_map.get(attempt_id)
        if db_id is None:
            # attempt_id not known — check if it was created in a previous
            # server run (won't happen with current stub auth, but handle it)
            return None

        db: Session = SessionLocal()
        try:
            row = db.query(ExamSessionModel).filter_by(id=db_id).first()
            if row is None:
                return None
            attempt = self._session_to_attempt(row)
            self._cache[attempt_id] = attempt
            return attempt
        finally:
            db.close()

    def get_by_exam_and_student(
        self, exam_id: str, student_id: str
    ) -> Optional[Attempt]:
        # Check cache first
        for attempt in self._cache.values():
            if attempt.exam_id == exam_id and attempt.student_id == student_id:
                return attempt

        # Check DB
        try:
            db_exam_id = int(exam_id)
        except ValueError:
            db: Session = SessionLocal()
            try:
                row = db.query(ExamModel).first()
                db_exam_id = row.id if row else 1
            finally:
                db.close()

        try:
            db_user_id = int(student_id)
        except ValueError:
            db_user_id = 1

        db: Session = SessionLocal()
        try:
            row = db.query(ExamSessionModel).filter_by(
                exam_id=db_exam_id,
                user_id=db_user_id,
                status="IN_PROGRESS",
            ).order_by(ExamSessionModel.started_at.desc()).first()

            if row is None:
                return None

            str_id = f"attempt_{row.id}"
            self._id_map[str_id] = row.id
            attempt = self._session_to_attempt(row)
            attempt.id = str_id
            self._cache[str_id] = attempt
            return attempt
        finally:
            db.close()

    def list_by_student(self, student_id: str) -> list[Attempt]:
        try:
            db_user_id = int(student_id)
        except ValueError:
            db_user_id = 1

        db: Session = SessionLocal()
        try:
            rows = db.query(ExamSessionModel).filter_by(user_id=db_user_id).all()
            result = []
            for row in rows:
                str_id = f"attempt_{row.id}"
                self._id_map[str_id] = row.id
                attempt = self._session_to_attempt(row)
                attempt.id = str_id
                self._cache[str_id] = attempt
                result.append(attempt)
            return result
        finally:
            db.close()


# ─────────────────────────────────────────────────────────────────────────────
# AUDIO TRACKER
# ─────────────────────────────────────────────────────────────────────────────

class PostgresAudioTracker:
    """
    Persists audio play counts to audio_play_logs.
    Uses an in-process cache keyed by (attempt_id, question_id).
    """

    MAX_PLAYS: int = 2

    def __init__(self) -> None:
        self._cache: dict[tuple[str, str], int] = {}
        # maps (str_attempt_id, str_question_id) → db row id
        self._row_map: dict[tuple[str, str], int] = {}

    def _db_ids(
        self, attempt_id: str, question_id: str, db: Session
    ) -> tuple[Optional[int], Optional[int]]:
        """Resolve string attempt/question IDs to integer DB ids."""
        # attempt_id like "attempt_3" → integer 3
        try:
            db_attempt_id = int(attempt_id.replace("attempt_", ""))
        except ValueError:
            return None, None
        try:
            db_question_id = int(question_id)
        except ValueError:
            return None, None
        return db_attempt_id, db_question_id

    def get_plays(self, attempt_id: str, question_id: str) -> int:
        key = (attempt_id, question_id)
        if key in self._cache:
            return self._cache[key]

        db: Session = SessionLocal()
        try:
            db_attempt_id, db_question_id = self._db_ids(attempt_id, question_id, db)
            if db_attempt_id is None:
                return 0
            row = db.query(AudioPlayLogModel).filter_by(
                attempt_id=db_attempt_id,
                question_id=db_question_id,
            ).first()
            count = row.play_count if row else 0
            self._cache[key] = count
            if row:
                self._row_map[key] = row.id
            return count
        finally:
            db.close()

    def record_play(self, attempt_id: str, question_id: str) -> int:
        key = (attempt_id, question_id)
        current = self.get_plays(attempt_id, question_id)

        if current >= self.MAX_PLAYS:
            raise ValueError(
                f"Maximum audio plays ({self.MAX_PLAYS}) reached "
                f"for question {question_id}."
            )

        new_count = current + 1
        self._cache[key] = new_count

        db: Session = SessionLocal()
        try:
            db_attempt_id, db_question_id = self._db_ids(attempt_id, question_id, db)
            if db_attempt_id is None:
                return new_count

            row_id = self._row_map.get(key)
            if row_id:
                row = db.query(AudioPlayLogModel).filter_by(id=row_id).first()
                if row:
                    row.play_count = new_count
            else:
                row = db.query(AudioPlayLogModel).filter_by(
                    attempt_id=db_attempt_id,
                    question_id=db_question_id,
                ).first()
                if row:
                    row.play_count = new_count
                    self._row_map[key] = row.id
                else:
                    new_row = AudioPlayLogModel(
                        attempt_id=db_attempt_id,
                        question_id=db_question_id,
                        play_count=new_count,
                    )
                    db.add(new_row)
                    db.flush()
                    self._row_map[key] = new_row.id

            db.commit()
        except Exception:
            db.rollback()
            self._cache[key] = current   # rollback cache too
            raise
        finally:
            db.close()

        return new_count

    def plays_remaining(self, attempt_id: str, question_id: str) -> int:
        return self.MAX_PLAYS - self.get_plays(attempt_id, question_id)

    def can_play(self, attempt_id: str, question_id: str) -> bool:
        return self.get_plays(attempt_id, question_id) < self.MAX_PLAYS
