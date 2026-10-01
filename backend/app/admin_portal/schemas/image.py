from datetime import datetime

from pydantic import BaseModel, Field


class ImageCreate(BaseModel):
    file_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
    )

    file_url: str = Field(
        ...,
        min_length=1,
    )


class ImageUpdate(BaseModel):
    file_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    file_url: str | None = Field(
        default=None,
        min_length=1,
    )


class ImageResponse(BaseModel):
    id: int
    file_name: str
    file_url: str
    created_at: datetime | None = None