"""Import every ORM mapping so Alembic discovers the unified metadata."""

from .user import User, UserModel
from .password_reset_otp import PasswordResetOTP
from .orm import (
    AudioPlayLogModel,
    ExamModel,
    ExamSessionModel,
    ExamSetModel,
    ImageModel,
    OptionModel,
    QuestionModel,
    ResultModel,
    StudentAnswerModel,
)

__all__ = [
    "AudioPlayLogModel", "ExamModel", "ExamSessionModel", "ExamSetModel",
    "ImageModel", "OptionModel", "PasswordResetOTP", "QuestionModel",
    "ResultModel", "StudentAnswerModel", "User", "UserModel",
]
