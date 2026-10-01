from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class ExamSet(Base):
    __tablename__ = "exam_sets"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    exam_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("exams.id"),
        nullable=False,
    )

    set_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    set_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    created_by: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
    )

    created_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )