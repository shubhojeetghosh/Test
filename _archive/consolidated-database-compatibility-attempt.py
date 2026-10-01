"""Compatibility imports for the consolidated database layer.

The one SQLAlchemy engine, session factory, declarative base, and request
dependency live in :mod:`app.database.database`.  Student modules retain
their established imports through this small compatibility module.
"""

from app.database.database import Base, SessionLocal, engine, get_db

__all__ = ["Base", "SessionLocal", "engine", "get_db"]
