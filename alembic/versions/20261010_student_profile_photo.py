"""Add the profile photo reference used by the student profile endpoint."""

from typing import Sequence, Union

from alembic import op


revision: str = "20261010_student_profile_photo"
down_revision: Union[str, Sequence[str], None] = "20261008_restore_student_login"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Idempotent because some deployments apply the companion SQL migration
    # directly before Alembic is advanced.
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_photo_url TEXT")


def downgrade() -> None:
    # Keep stored profile-photo references intact on downgrade.
    pass
