from app.core.database import SessionLocal
from app.repository.database_exam import DatabaseExamRepository


def main() -> None:
    db = SessionLocal()

    try:
        repository = DatabaseExamRepository(db)

        # Replace 1 with an actual exam ID from your exams table.
        exam = repository.get_exam("1")

        if exam is None:
            print("Exam not found.")
            return

        print("Exam loaded successfully")
        print(f"ID: {exam.id}")
        print(f"Title: {exam.title}")
        print(f"Questions: {len(exam.questions)}")

        for question in exam.questions:
            print(
                f"Question {question.question_number}: "
                f"{question.text}"
            )
            print(f"Options: {len(question.options)}")

    finally:
        db.close()


if __name__ == "__main__":
    main()