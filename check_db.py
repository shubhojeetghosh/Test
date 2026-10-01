import os, sys
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "backend", ".env"))
url = os.getenv("DATABASE_URL", "").replace("channel_binding=require", "channel_binding=disable")

import sqlalchemy as sa
engine = sa.create_engine(url, echo=False)

tables = ["exams", "exam_sets", "questions", "options", "images",
          "exam_sessions", "student_answers", "audio_play_logs", "results", "users"]

with engine.connect() as conn:
    for t in tables:
        rows = conn.execute(sa.text(
            f"SELECT column_name, data_type, is_nullable "
            f"FROM information_schema.columns "
            f"WHERE table_schema='public' AND table_name='{t}' "
            f"ORDER BY ordinal_position"
        ))
        cols = rows.fetchall()
        if cols:
            print(f"\n--- {t} ---")
            for col in cols:
                print(f"  {col[0]:30s} {col[1]:20s} nullable={col[2]}")
        else:
            print(f"\n--- {t} --- NOT FOUND")
