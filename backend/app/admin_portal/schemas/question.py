from datetime import datetime

from pydantic import BaseModel, Field


class OptionCreate(BaseModel):
    option_label: str = Field(..., min_length=1, max_length=1)
    option_text: str | None = None
    image_url: str | None = None
    audio_url: str | None = None
    is_correct: bool = False
    image_id: int | None = None


class OptionUpdate(BaseModel):
    option_label: str | None = Field(
        default=None,
        min_length=1,
        max_length=1,
    )
    option_text: str | None = None
    image_url: str | None = None
    audio_url: str | None = None
    is_correct: bool | None = None
    image_id: int | None = None


class QuestionCreate(BaseModel):
    exam_id: int
    question_number: int = Field(..., gt=0)
    question_type: str = Field(..., max_length=30)
    question_text: str | None = None
    image_url: str | None = None
    audio_url: str | None = None
    marks: float = Field(..., ge=0)
    created_by: int | None = None
    set_id: int | None = None
    status: str | None = Field(
        default="DRAFT",
        max_length=20,
    )
    options: list[OptionCreate] = []


class QuestionUpdate(BaseModel):
    question_number: int | None = Field(
        default=None,
        gt=0,
    )
    question_type: str | None = Field(
        default=None,
        max_length=30,
    )
    question_text: str | None = None
    image_url: str | None = None
    audio_url: str | None = None
    marks: float | None = Field(
        default=None,
        ge=0,
    )
    set_id: int | None = None
    status: str | None = Field(
        default=None,
        max_length=20,
    )


class OptionResponse(BaseModel):
    id: int
    question_id: int
    option_label: str
    option_text: str | None = None
    image_url: str | None = None
    audio_url: str | None = None
    is_correct: bool
    image_id: int | None = None


class QuestionResponse(BaseModel):
    id: int
    exam_id: int
    question_number: int
    question_type: str
    question_text: str | None = None
    image_url: str | None = None
    audio_url: str | None = None
    marks: float
    created_at: datetime | None = None
    created_by: int | None = None
    set_id: int | None = None
    status: str | None = None
    options: list[OptionResponse] = []