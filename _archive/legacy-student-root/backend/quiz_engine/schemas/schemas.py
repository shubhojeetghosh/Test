from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from backend.quiz_engine.question import QuestionType


# ─────────────────────────────────────────
# QUIZ SCHEMAS
# ─────────────────────────────────────────

class QuizSummaryResponse(BaseModel):
    id: str
    title: str
    duration_minutes: int
    total_questions: int
    total_marks: float


class QuizDetailResponse(BaseModel):
    id: str
    title: str
    duration_minutes: int
    total_questions: int
    marks_per_question: float
    total_marks: float


# ─────────────────────────────────────────
# OPTION AND QUESTION SCHEMAS
# NOTE: is_correct is intentionally excluded
# ─────────────────────────────────────────

class OptionResponse(BaseModel):
    id: str
    text: str
    audio_url: Optional[str] = None


class QuestionResponse(BaseModel):
    id: str
    question_number: int
    question_type: QuestionType
    text: str
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    options: list[OptionResponse]


class QuestionsResponse(BaseModel):
    attempt_id: str
    questions: list[QuestionResponse]


# ─────────────────────────────────────────
# ATTEMPT SCHEMAS
# ─────────────────────────────────────────

class StartAttemptResponse(BaseModel):
    attempt_id: str
    exam_id: str
    status: str
    started_at: datetime
    expires_at: float
    duration_minutes: int


class AttemptStatusResponse(BaseModel):
    attempt_id: str
    status: str
    current_question: int
    time_remaining_seconds: int


class SubmitAttemptResponse(BaseModel):
    attempt_id: str
    status: str
    submitted_at: datetime


# ─────────────────────────────────────────
# ANSWER SCHEMAS
# ─────────────────────────────────────────

class SubmitAnswerRequest(BaseModel):
    question_id: str
    selected_option_id: str


class SubmitAnswerResponse(BaseModel):
    question_id: str
    selected_option_id: str
    answered_at: datetime


# ─────────────────────────────────────────
# AUDIO SCHEMAS
# ─────────────────────────────────────────

class AudioPlayRequest(BaseModel):
    question_id: str


class AudioPlayResponse(BaseModel):
    question_id: str
    plays_used: int
    plays_remaining: int
    allowed: bool


# ─────────────────────────────────────────
# ERROR SCHEMA
# ─────────────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str