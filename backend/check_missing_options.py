from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.admin_portal.models.question import Question
from app.admin_portal.models.option import Option


def main() -> None:
    db = SessionLocal()

    try:
        statement = (
            select(
                Question.id,
                Question.exam_id,
                Question.question_number,
                Question.question_text,
                func.count(Option.id).label("option_count"),
            )
            .outerjoin(
                Option,
                Option.question_id == Question.id,
            )
            .where(Question.exam_id == 1)
            .group_by(
                Question.id,
                Question.exam_id,
                Question.question_number,
                Question.question_text,
            )
            .order_by(Question.question_number)
        )

        rows = db.execute(statement).all()

        if not rows:
            print("No questions found for exam ID 1.")
            return

        for row in rows:
            print(
                f"Question ID: {row.id} | "
                f"Number: {row.question_number} | "
                f"Options: {row.option_count} | "
                f"Text: {row.question_text!r}"
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()