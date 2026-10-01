from .attempt import Attempt
from .exam import Exam


class QuizEngine:
    def __init__(self, exam: Exam):
        self.exam = exam

    def start_attempt(self, attempt: Attempt) -> Attempt:
        if attempt.exam_id != self.exam.id:
            raise ValueError("Attempt does not belong to this exam.")

        self.exam.validate()
        attempt.start(self.exam.duration_minutes)

        return attempt

    def get_question(self, question_number: int):
        if question_number < 1 or question_number > self.exam.total_questions:
            raise ValueError("Invalid question number.")

        return next(
            question
            for question in self.exam.questions
            if question.question_number == question_number
        )

    def answer_question(
        self,
        attempt: Attempt,
        question_id: str,
        option_id: str,
    ) -> None:
        question = next(
            (q for q in self.exam.questions if q.id == question_id),
            None,
        )

        if question is None:
            raise ValueError(f"Question not found: {question_id}")

        if not any(option.id == option_id for option in question.options):
            raise ValueError(f"Invalid option: {option_id}")

        attempt.save_answer(question_id, option_id)

    def next_question(self, attempt: Attempt) -> int:
        if attempt.current_question >= self.exam.total_questions:
            return attempt.current_question

        attempt.current_question += 1
        return attempt.current_question

    def previous_question(self, attempt: Attempt) -> int:
        if attempt.current_question <= 1:
            return attempt.current_question

        attempt.current_question -= 1
        return attempt.current_question

    def submit_attempt(self, attempt: Attempt) -> None:
        attempt.submit()