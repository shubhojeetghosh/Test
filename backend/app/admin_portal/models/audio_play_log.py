from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class AudioPlayLog(Base):
    __tablename__ = "audio_play_logs"

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

    option_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("options.id"),
        nullable=True,
    )

    play_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )