from backend.quiz_engine.database import SessionLocal
from sqlalchemy import text

print("=" * 60)
print("TESTING SUPABASE POSTGRESQL CONNECTION")
print("=" * 60)

db = None

try:
    # Test 1: Connection
    print("\n[1] Testing database connection...")
    db = SessionLocal()
    result = db.execute(text("SELECT 1"))
    print("    SUCCESS: Database connection works!")

    # Test 2: Get PostgreSQL tables
    print("\n[2] Fetching tables...")

    result = db.execute(
        text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
    )

    tables = [row[0] for row in result]

    if not tables:
        print("    WARNING: No tables found in public schema.")
    else:
        print(f"    SUCCESS: Found {len(tables)} table(s):")
        for table in tables:
            print(f"       - {table}")

    # Test 3: Required Quiz Engine tables
    print("\n[3] Checking required Quiz Engine tables...")

    required_tables = [
        "questions",
        "options",
        "exam_sessions",
        "student_answers",
        "audio_play_logs",
        "results",
    ]

    missing = []

    for table in required_tables:
        if table in tables:
            print(f"    SUCCESS: {table}")
        else:
            print(f"    MISSING: {table}")
            missing.append(table)

    if missing:
        print("\nWARNING: Missing tables:")
        for table in missing:
            print(f"    - {table}")
    else:
        print("\nSUCCESS: All required tables exist!")

except Exception as e:
    print("\nDATABASE CONNECTION FAILED")
    print(str(e))

finally:
    if db:
        db.close()

print("\n" + "=" * 60)