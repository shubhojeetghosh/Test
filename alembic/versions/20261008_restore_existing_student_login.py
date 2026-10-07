"""Restore email verification for student accounts already in the user table.

New registrations are kept in pending_student_registrations until OTP verification,
so existing student rows represent accounts created by the earlier registration flow.
"""

from typing import Sequence, Union

from alembic import op


revision: str = "20261008_restore_student_login"
down_revision: Union[str, Sequence[str], None] = "20261007_set_purchase_requests"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE users SET email_verified = TRUE "
        "WHERE lower(role) = 'student' AND email_verified = FALSE"
    )


def downgrade() -> None:
    # Do not revoke verification from existing accounts on downgrade.
    pass
