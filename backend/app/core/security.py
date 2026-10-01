from passlib.context import CryptContext
from jose import jwt, JWTError

from app.core.config import settings


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

def create_access_token(data: dict) -> str:
    """
    Create a JWT access token.
    """

    to_encode = data.copy()

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.
    """

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        return payload

    except JWTError:
        raise
