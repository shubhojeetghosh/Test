"""add student email verification state and OTP purpose

Revision ID: a91f2d6c0e43
Revises: da1505b5b381
"""
from typing import Sequence, Union

from alembic import op


revision: str = "a91f2d6c0e43"
down_revision: Union[str, Sequence[str], None] = "20261001_attempt_integrity"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS "
        "email_verified BOOLEAN NOT NULL DEFAULT TRUE"
    )
    op.execute(
        "ALTER TABLE password_reset_otps ADD COLUMN IF NOT EXISTS "
        "purpose VARCHAR(30) NOT NULL DEFAULT 'password_reset'"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_password_reset_otps_user_purpose_used "
        "ON password_reset_otps (user_id, purpose, used)"
    )


def downgrade() -> None:
    op.drop_index("ix_password_reset_otps_user_purpose_used", table_name="password_reset_otps")
    op.drop_column("password_reset_otps", "purpose")
    op.drop_column("users", "email_verified")
