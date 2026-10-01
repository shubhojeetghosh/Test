from sqlalchemy import Column, Integer, String, DateTime
from backend.authentication.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    roll_no = Column(String, unique=True, nullable=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="student", nullable=False)

    otp = Column(String, nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)