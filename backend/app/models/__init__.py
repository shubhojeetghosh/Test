"""Import every ORM mapping so Alembic discovers the unified metadata."""

from .user import User, UserModel
from .password_reset_otp import PasswordResetOTP
from .pending_student_registration import PendingStudentRegistration
from .student_set_purchase_request import StudentSetPurchaseRequest
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
    "ImageModel", "OptionModel", "PasswordResetOTP", "PendingStudentRegistration", "QuestionModel",
    "ResultModel", "StudentAnswerModel", "StudentSetPurchaseRequest", "User", "UserModel",
]
