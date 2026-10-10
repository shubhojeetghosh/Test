"""Unified SQLAlchemy user model for authentication and quiz sessions."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    """Single mapping for ``users`` used by both original backend areas."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    roll_no: Mapped[Optional[str]] = mapped_column(String, unique=True, nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    profile_photo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="student")
    # Existing accounts remain active when this column is added; new student
    # registrations explicitly set it to False until their email is verified.
    email_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    otp: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    otp_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now())
    student_id: Mapped[Optional[int]] = mapped_column(Integer, unique=True)

    sessions: Mapped[list["ExamSessionModel"]] = relationship(back_populates="user")


# Compatibility name used by the original PostgreSQL quiz repository.
UserModel = User
