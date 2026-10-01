from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class QuestionType(str, Enum):
    READING = "reading"
    IMAGE = "image"
    IMAGE_AUDIO = "image_audio"
    AUDIO_OPTION = "audio_option"


@dataclass(frozen=True)
class Option:
    id: str
    text: str
    is_correct: bool = False
    audio_url: Optional[str] = None


@dataclass
class Question:
    id: str
    question_number: int
    question_type: QuestionType
    text: str
    marks: float = 2.5
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    options: list[Option] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.question_number < 1:
            raise ValueError("Question number must be at least 1.")

        if self.marks <= 0:
            raise ValueError("Question marks must be greater than 0.")

        if not self.options:
            raise ValueError("A question must contain at least one option.")

    def get_correct_option(self) -> Optional[Option]:
        return next(
            (option for option in self.options if option.is_correct),
            None,
        )

    def is_correct(self, option_id: str) -> bool:
        option = next(
            (option for option in self.options if option.id == option_id),
            None,
        )

        if option is None:
            raise ValueError(f"Invalid option: {option_id}")

        return option.is_correct