from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class Option(Base):
    __tablename__ = "options"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    question_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("questions.id"),
        nullable=False,
    )

    option_label: Mapped[str] = mapped_column(
        String(1),
        nullable=False,
    )

    option_text: Mapped[str | None] = mapped_column(
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

    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    image_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )