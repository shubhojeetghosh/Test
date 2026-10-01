from backend.quiz_engine.exam import Exam
from backend.quiz_engine.attempt import Attempt


class QuizScorer:
    def __init__(self, exam: Exam):
        self.exam = exam

    def calculate_score(self, attempt: Attempt) -> float:
        score = 0.0

        for question in self.exam.questions:
            answer = attempt.answers.get(question.id)

            if answer is None:
                continue

            if answer.selected_option_id is None:
                continue

            if question.is_correct(answer.selected_option_id):
                score += question.marks

        return score

    def calculate_percentage(self, attempt: Attempt) -> float:
        if self.exam.total_marks == 0:
            return 0.0

        score = self.calculate_score(attempt)

        return (score / self.exam.total_marks) * 100