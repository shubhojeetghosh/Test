from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # =========================================================
    # DATABASE
    # =========================================================

    DATABASE_URL: str


    # =========================================================
    # SECURITY / JWT
    # =========================================================

    SECRET_KEY: str
    SECRET_KEY_PREVIOUS: str | None = None

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60


    # =========================================================
    # GMAIL SMTP
    # =========================================================

    SMTP_HOST: str = "smtp.gmail.com"

    SMTP_PORT: int = 587

    SMTP_USERNAME: str

    SMTP_PASSWORD: str

    SMTP_FROM_EMAIL: str = Field(
        validation_alias=AliasChoices("SMTP_FROM_EMAIL", "MAIL_FROM")
    )

    SMTP_FROM_NAME: str = "EPS TOPIK EXAM"

    # Recipients for the two-person approval step in admin onboarding.
    ADMIN_EMAIL: str = ""
    DEVELOPER_EMAIL: str = ""

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


    # =========================================================
    # ADMIN PASSWORD RESET
    # =========================================================
    #
    # URL of the frontend page where an admin can enter
    # their new password after clicking the reset link.
    #
    # This can be overridden in .env
    # =========================================================

    ADMIN_RESET_PASSWORD_URL: str = (
        "http://127.0.0.1:5500/admin-reset-password.html"
    )


    # =========================================================
    # ENVIRONMENT FILE
    # =========================================================

    model_config = SettingsConfigDict(
        env_file=(
            Path(__file__).resolve().parents[3] / ".env",
            Path(__file__).resolve().parents[4] / ".env",
        ),
        extra="ignore",
    )


settings = Settings()
