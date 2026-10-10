from pathlib import Path
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    SECRET_KEY_PREVIOUS: Optional[str] = None
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    STUDENT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 180
    OTP_EXPIRE_MINUTES: int = 5
    OTP_RESEND_COOLDOWN_SECONDS: int = 30
    OTP_MAX_ATTEMPTS: int = 5
    SUPABASE_URL: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_MEDIA_BUCKET: str = "exam-media"
    ZEROBOUNCE_API_KEY: Optional[str] = None

    @field_validator("SECRET_KEY")
    @classmethod
    def require_strong_secret(cls, value: str) -> str:
        if len(value.encode("utf-8")) < 32 or value.strip().lower() in {
            "changeme", "secret", "your-secret-key", "replace-me"
        }:
            raise ValueError("SECRET_KEY must be a unique secret of at least 32 bytes.")
        return value

    @field_validator("ALGORITHM")
    @classmethod
    def require_supported_jwt_algorithm(cls, value: str) -> str:
        if value != "HS256":
            raise ValueError("Only HS256 is supported for JWT signing.")
        return value

    model_config = SettingsConfigDict(
        env_file=(
            Path(__file__).resolve().parents[2] / ".env",
            Path(__file__).resolve().parents[3] / ".env",
        ),
        extra="ignore"
    )


settings = Settings()
