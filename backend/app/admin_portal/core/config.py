from pathlib import Path

from pydantic import AliasChoices, Field
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

    SMTP_FROM_NAME: str = "EPS-TOPIK"


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
        env_file=Path(__file__).resolve().parents[3] / ".env",
        extra="ignore",
    )


settings = Settings()
