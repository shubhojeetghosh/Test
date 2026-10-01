from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    exam_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("exams.id"),
        nullable=False,
    )

    question_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    question_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    question_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    image_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    audio_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    marks: Mapped[Decimal] = mapped_column(
        Numeric(3, 1),
        nullable=False,
    )

    created_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
    )

    set_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("exam_sets.id"),
        nullable=True,
    )

    status: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )