from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


def _pool_setting(name: str, default: int, minimum: int = 0) -> int:
    import os

    try:
        return max(minimum, int(os.getenv(name, str(default))))
    except ValueError:
        return default


# One modest pool per worker keeps horizontally scaled deployments within
# typical PostgreSQL connection budgets. Override with environment variables.
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=_pool_setting("DB_POOL_RECYCLE", 300, 1),
    pool_size=_pool_setting("DB_POOL_SIZE", 3, 1),
    max_overflow=_pool_setting("DB_MAX_OVERFLOW", 2),
    pool_timeout=_pool_setting("DB_POOL_TIMEOUT", 10, 1),
    connect_args={"connect_timeout": 10},
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
