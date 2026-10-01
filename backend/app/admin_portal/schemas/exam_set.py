from datetime import datetime

from pydantic import BaseModel, Field


class ExamSetCreate(BaseModel):
    set_number: int = Field(..., gt=0)
    set_name: str = Field(..., min_length=1, max_length=100)
    created_by: int | None = None


class ExamSetUpdate(BaseModel):
    set_number: int | None = Field(
        default=None,
        gt=0,
    )

    set_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )


class ExamSetResponse(BaseModel):
    id: int
    exam_id: int
    set_number: int
    set_name: str
    created_by: int | None = None
    created_at: datetime | None = None