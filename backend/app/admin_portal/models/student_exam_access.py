from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class StudentExamAccess(Base):
    __tablename__ = "student_exam_access"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    exam_set_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("exam_sets.id"),
        nullable=False,
    )

    unlocked_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    unlocked_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "exam_set_id",
            name="uq_student_exam_set_access",
        ),
    )