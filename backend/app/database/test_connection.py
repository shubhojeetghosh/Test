from sqlalchemy import text

from app.database.database import engine


def test_database():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print("Database connection:", result.scalar())

        tables = connection.execute(
            text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
        )

        print("\nExisting tables:")

        for row in tables:
            print(f"- {row[0]}")


if __name__ == "__main__":
    test_database()