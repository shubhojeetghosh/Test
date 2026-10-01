from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class StudentAnswer(Base):
    __tablename__ = "student_answers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    attempt_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("exam_sessions.id"),
        nullable=False,
    )

    question_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("questions.id"),
        nullable=False,
    )

    selected_option_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("options.id"),
        nullable=True,
    )

    answered_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )