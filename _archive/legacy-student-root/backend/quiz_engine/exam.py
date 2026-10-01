from dataclasses import dataclass, field

from .question import Question


@dataclass
class Exam:
    id: str
    title: str
    duration_minutes: int = 50
    total_questions: int = 40
    marks_per_question: float = 2.5
    questions: list[Question] = field(default_factory=list)

    @property
    def total_marks(self) -> float:
        return self.total_questions * self.marks_per_question

    def add_question(self, question: Question) -> None:
        if len(self.questions) >= self.total_questions:
            raise ValueError(
                "Exam already contains the maximum number of questions."
            )

        self.questions.append(question)

    def validate(self) -> None:
        if len(self.questions) != self.total_questions:
            raise ValueError(
                f"Exam must contain exactly {self.total_questions} questions."
            )

        numbers = [question.question_number for question in self.questions]

        if len(set(numbers)) != len(numbers):
            raise ValueError("Question numbers must be unique.")

        if sorted(numbers) != list(range(1, self.total_questions + 1)):
            raise ValueError(
                f"Questions must be numbered from 1 to {self.total_questions}."
            )