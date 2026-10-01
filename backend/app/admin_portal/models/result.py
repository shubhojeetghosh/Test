from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class Result(Base):
    __tablename__ = "results"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    attempt_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("exam_sessions.id"),
        nullable=False,
    )

    total_questions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    correct_answers: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    wrong_answers: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    unanswered: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    created_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )