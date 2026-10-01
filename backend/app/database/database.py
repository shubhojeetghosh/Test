from sqlalchemy.orm import DeclarativeBase

from app.core.database import SessionLocal, engine


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
