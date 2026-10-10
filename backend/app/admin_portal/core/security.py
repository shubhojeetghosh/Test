from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext

from app.admin_portal.core.config import settings
from app.core.jwt_tokens import decode_hs256, encode_hs256


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return pwd_context.verify(
        plain_password,
        hashed_password,
    )


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(
    user_id: int,
    role: str,
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
    }

    return encode_hs256(payload, settings.SECRET_KEY)


def decode_access_token(token: str) -> dict:
    keys = [settings.SECRET_KEY]
    if settings.SECRET_KEY_PREVIOUS:
        keys.append(settings.SECRET_KEY_PREVIOUS)
    return decode_hs256(token, keys)
