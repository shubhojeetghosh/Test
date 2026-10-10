from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext

from app.core.config import settings
from app.core.jwt_tokens import decode_hs256, encode_hs256


# ============================================================
# PASSWORD HASHING
# ============================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """
    Hash a user's password using bcrypt.
    """
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against its bcrypt hash.
    """
    return pwd_context.verify(password, hashed_password)


# ============================================================
# OTP HASHING
# ============================================================

def hash_otp(otp: str) -> str:
    """
    Hash a password-reset OTP using bcrypt.
    """
    return pwd_context.hash(otp)


def verify_otp(otp: str, hashed_otp: str) -> bool:
    """
    Verify an OTP against its stored hash.
    """
    return pwd_context.verify(otp, hashed_otp)


# ============================================================
# JWT ACCESS TOKEN
# ============================================================

def create_access_token(data: dict, expires_minutes: int | None = None) -> str:
    """
    Create a JWT access token.
    """

    to_encode = data.copy()
    to_encode.setdefault(
        "exp",
        datetime.now(timezone.utc)
        + timedelta(minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return encode_hs256(to_encode, settings.SECRET_KEY)


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.
    """

    keys = [settings.SECRET_KEY]
    if settings.SECRET_KEY_PREVIOUS:
        keys.append(settings.SECRET_KEY_PREVIOUS)
    return decode_hs256(token, keys)
