"""
SQLAlchemy ORM models
=====================
Mirrors the Neon PostgreSQL schema exactly.
Table names match what was confirmed by inspection:
  exams, exam_sets, questions, options, images,
  exam_sessions, student_answers, audio_play_logs, results, users
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.quiz_engine.database import Base


# ─────────────────────────────────────────
# USERS
# ─────────────────────────────────────────

class UserModel(Base):
    __tablename__ = "users"

    id:           Mapped[int]           = mapped_column(Integer, primary_key=True)
    name:         Mapped[str]           = mapped_column(String(100), nullable=False)
    email:        Mapped[str]           = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash:Mapped[str]           = mapped_column(Text, nullable=False)
    role:         Mapped[str]           = mapped_column(String(20), nullable=False, default="student")
    created_at:   Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now())
    student_id:   Mapped[Optional[int]] = mapped_column(Integer, unique=True)

    sessions: Mapped[list["ExamSessionModel"]] = relationship(back_populates="user")


# ─────────────────────────────────────────
# EXAMS
# ─────────────────────────────────────────

class ExamModel(Base):
    __tablename__ = "exams"

    id:               Mapped[int]           = mapped_column(Integer, primary_key=True)
    title:            Mapped[str]           = mapped_column(String(150), nullable=False)
    duration_minutes: Mapped[int]           = mapped_column(Integer, nullable=False)
    total_questions:  Mapped[int]           = mapped_column(Integer, nullable=False)
    total_marks:      Mapped[float]         = mapped_column(Numeric(6, 2), nullable=False)
    created_at:       Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now())

    questions: Mapped[list["QuestionModel"]] = relationship(back_populates="exam", order_by="QuestionModel.question_number")
    sets:      Mapped[list["ExamSetModel"]]  = relationship(back_populates="exam")
    sessions:  Mapped[list["ExamSessionModel"]] = relationship(back_populates="exam")


# ─────────────────────────────────────────
# EXAM SETS
# ─────────────────────────────────────────

class ExamSetModel(Base):
    __tablename__ = "exam_sets"
    __table_args__ = (UniqueConstraint("exam_id", "set_number", name="unique_exam_set"),)

    id:         Mapped[int]           = mapped_column(Integer, primary_key=True)
    exam_id:    Mapped[int]           = mapped_column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    set_number: Mapped[int]           = mapped_column(Integer, nullable=False)
    set_name:   Mapped[str]           = mapped_column(String(100), nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now())

    exam: Mapped["ExamModel"] = relationship(back_populates="sets")


# ─────────────────────────────────────────
# IMAGES
# ─────────────────────────────────────────

class ImageModel(Base):
    __tablename__ = "images"

    id:         Mapped[int]           = mapped_column(Integer, primary_key=True)
    file_name:  Mapped[str]           = mapped_column(String(255), nullable=False)
    file_url:   Mapped[str]           = mapped_column(Text, nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now())

    options: Mapped[list["OptionModel"]] = relationship(back_populates="image")


# ─────────────────────────────────────────
# QUESTIONS
# ─────────────────────────────────────────

class QuestionModel(Base):
    __tablename__ = "questions"
    __table_args__ = (
        UniqueConstraint("exam_id", "question_number", name="unique_question_number"),
        CheckConstraint("status IN ('DRAFT','PUBLISHED','ARCHIVED')", name="valid_question_status"),
    )

    id:              Mapped[int]           = mapped_column(Integer, primary_key=True)
    exam_id:         Mapped[int]           = mapped_column(Integer, ForeignKey("exams.id"), nullable=False)
    question_number: Mapped[int]           = mapped_column(Integer, nullable=False)
    question_type:   Mapped[str]           = mapped_column(String(30), nullable=False)
    question_text:   Mapped[Optional[str]] = mapped_column(Text)
    image_url:       Mapped[Optional[str]] = mapped_column(Text)
    audio_url:       Mapped[Optional[str]] = mapped_column(Text)
    marks:           Mapped[float]         = mapped_column(Numeric(3, 1), nullable=False, default=2.5)
    created_at:      Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now())
    created_by:      Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    set_id:          Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("exam_sets.id", ondelete="CASCADE"))
    status:          Mapped[Optional[str]] = mapped_column(String(20), default="PUBLISHED")

    exam:    Mapped["ExamModel"]       = relationship(back_populates="questions")
    options: Mapped[list["OptionModel"]] = relationship(back_populates="question", cascade="all, delete-orphan")


# ─────────────────────────────────────────
# OPTIONS
# ─────────────────────────────────────────

class OptionModel(Base):
    __tablename__ = "options"
    __table_args__ = (UniqueConstraint("question_id", "option_label", name="unique_option_label"),)

    id:           Mapped[int]           = mapped_column(Integer, primary_key=True)
    question_id:  Mapped[int]           = mapped_column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    option_label: Mapped[str]           = mapped_column(String(1), nullable=False)
    option_text:  Mapped[Optional[str]] = mapped_column(Text)
    image_url:    Mapped[Optional[str]] = mapped_column(Text)
    audio_url:    Mapped[Optional[str]] = mapped_column(Text)
    is_correct:   Mapped[bool]          = mapped_column(Boolean, nullable=False, default=False)
    image_id:     Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("images.id", ondelete="SET NULL"))

    question: Mapped["QuestionModel"] = relationship(back_populates="options")
    image:    Mapped[Optional["ImageModel"]] = relationship(back_populates="options")


# ─────────────────────────────────────────
# EXAM SESSIONS  (= exam_attempts in domain)
# ─────────────────────────────────────────

class ExamSessionModel(Base):
    __tablename__ = "exam_sessions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('IN_PROGRESS','SUBMITTED','AUTO_SUBMITTED')",
            name="valid_attempt_status",
        ),
    )

    id:           Mapped[int]           = mapped_column(Integer, primary_key=True)
    user_id:      Mapped[int]           = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    exam_id:      Mapped[int]           = mapped_column(Integer, ForeignKey("exams.id"), nullable=False)
    started_at:   Mapped[datetime]      = mapped_column(DateTime, server_default=func.now(), nullable=False)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    status:       Mapped[str]           = mapped_column(String(20), nullable=False, default="IN_PROGRESS")

    user:    Mapped["UserModel"]              = relationship(back_populates="sessions")
    exam:    Mapped["ExamModel"]              = relationship(back_populates="sessions")
    answers: Mapped[list["StudentAnswerModel"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    audio_plays: Mapped[list["AudioPlayLogModel"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    result:  Mapped[Optional["ResultModel"]] = relationship(back_populates="session", uselist=False)


# ─────────────────────────────────────────
# STUDENT ANSWERS  (= answers in domain)
# ─────────────────────────────────────────

class StudentAnswerModel(Base):
    __tablename__ = "student_answers"
    __table_args__ = (UniqueConstraint("attempt_id", "question_id", name="unique_attempt_question"),)

    id:                 Mapped[int]           = mapped_column(Integer, primary_key=True)
    attempt_id:         Mapped[int]           = mapped_column(Integer, ForeignKey("exam_sessions.id", ondelete="CASCADE"), nullable=False)
    question_id:        Mapped[int]           = mapped_column(Integer, ForeignKey("questions.id"), nullable=False)
    selected_option_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("options.id"))
    answered_at:        Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now())

    session:  Mapped["ExamSessionModel"] = relationship(back_populates="answers")
    question: Mapped["QuestionModel"]    = relationship()
    option:   Mapped[Optional["OptionModel"]] = relationship()


# ─────────────────────────────────────────
# AUDIO PLAY LOGS
# ─────────────────────────────────────────

class AudioPlayLogModel(Base):
    __tablename__ = "audio_play_logs"
    __table_args__ = (
        CheckConstraint("play_count >= 0 AND play_count <= 2", name="valid_play_count"),
    )

    id:          Mapped[int]           = mapped_column(Integer, primary_key=True)
    attempt_id:  Mapped[int]           = mapped_column(Integer, ForeignKey("exam_sessions.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[int]           = mapped_column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    option_id:   Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("options.id", ondelete="CASCADE"))
    play_count:  Mapped[int]           = mapped_column(Integer, nullable=False, default=0)

    session: Mapped["ExamSessionModel"] = relationship(back_populates="audio_plays")


# ─────────────────────────────────────────
# RESULTS
# ─────────────────────────────────────────

class ResultModel(Base):
    __tablename__ = "results"

    id:              Mapped[int]   = mapped_column(Integer, primary_key=True)
    attempt_id:      Mapped[int]   = mapped_column(Integer, ForeignKey("exam_sessions.id", ondelete="CASCADE"), nullable=False, unique=True)
    total_questions: Mapped[int]   = mapped_column(Integer, nullable=False)
    correct_answers: Mapped[int]   = mapped_column(Integer, nullable=False, default=0)
    wrong_answers:   Mapped[int]   = mapped_column(Integer, nullable=False, default=0)
    unanswered:      Mapped[int]   = mapped_column(Integer, nullable=False, default=0)
    score:           Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    percentage:      Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    created_at:      Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now())

    session: Mapped["ExamSessionModel"] = relationship(back_populates="result")
