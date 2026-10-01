from sqlalchemy import select

from app.core.database import SessionLocal
from app.admin_portal.models.question import Question
from app.admin_portal.models.option import Option


def main() -> None:
    db = SessionLocal()

    try:
        questions = (
            db.execute(
                select(Question)
                .where(Question.exam_id == 1)
                .where(Question.question_number >= 5)
                .order_by(Question.question_number)
            )
            .scalars()
            .all()
        )

        for question in questions:
            print("\n" + "=" * 60)
            print(f"Question ID: {question.id}")
            print(f"Question number: {question.question_number}")
            print(f"Question type: {question.question_type}")
            print(f"Question text: {question.question_text!r}")
            print(f"Image URL: {question.image_url!r}")
            print(f"Audio URL: {question.audio_url!r}")
            print(f"Marks: {question.marks}")

            options = (
                db.execute(
                    select(Option)
                    .where(Option.question_id == question.id)
                    .order_by(Option.id)
                )
                .scalars()
                .all()
            )

            print(f"Option count: {len(options)}")

            for option in options:
                print(
                    f"Option ID: {option.id} | "
                    f"Label: {option.option_label} | "
                    f"Text: {option.option_text!r} | "
                    f"Audio: {option.audio_url!r} | "
                    f"Correct: {option.is_correct}"
                )

    finally:
        db.close()


if __name__ == "__main__":
    main()