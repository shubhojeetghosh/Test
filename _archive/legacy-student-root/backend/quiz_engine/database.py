"""
Database Configuration
======================
SQLAlchemy engine + session factory for the Supabase PostgreSQL database.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# ── Load .env file ────────────────────────────────────────────────────────────

# The project .env is at the backend root.
_env_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", ".env")
)

load_dotenv(_env_path)


# ── Database URL ──────────────────────────────────────────────────────────────

DATABASE_URL = os.getenv("DATABASE_URL", "")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL not found. "
        "Ensure backend/.env exists with a valid DATABASE_URL."
    )


# ── SQLAlchemy Engine ─────────────────────────────────────────────────────────

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
)


# ── Test Supabase Database Connection ─────────────────────────────────────────

try:
    with engine.connect() as connection:

        result = connection.execute(
            text("SELECT current_database()")
        )

        print("DATABASE CONNECTED:", result.scalar())

except Exception as e:
    print("DATABASE CONNECTION FAILED:", e)


# ── Session Factory ───────────────────────────────────────────────────────────

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ── Declarative Base ──────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ── FastAPI Database Dependency ───────────────────────────────────────────────

def get_db():
    """
    Yields a database session for use in FastAPI route dependencies.
    Automatically closes the session after the request completes.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()