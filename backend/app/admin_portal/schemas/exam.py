from datetime import datetime

from pydantic import BaseModel, Field


class ExamCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    duration_minutes: int = Field(..., gt=0)
    total_questions: int = Field(..., gt=0)
    total_marks: float = Field(..., ge=0)
    status: str = Field(default="DRAFT", max_length=20)


class ExamUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    duration_minutes: int | None = Field(
        default=None,
        gt=0,
    )

    total_questions: int | None = Field(
        default=None,
        gt=0,
    )

    total_marks: float | None = Field(
        default=None,
        ge=0,
    )

    status: str | None = Field(
        default=None,
        max_length=20,
    )


class ExamResponse(BaseModel):
    id: int
    title: str
    duration_minutes: int
    total_questions: int
    total_marks: float
    status: str
    created_at: datetime | None = None