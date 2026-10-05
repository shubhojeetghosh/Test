"""Compatibility marker for the already-stamped attempt integrity revision.

The configured database reports this revision, but its original migration file
is absent from the repository. Keep the database's revision identifier intact
and provide the missing graph node so later migrations can run. The underlying
database changes are managed separately in backend/migrations SQL files.
"""

from typing import Sequence, Union

from alembic import op


revision: str = "20261001_attempt_integrity"
down_revision: Union[str, Sequence[str], None] = "da1505b5b381"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The database is already stamped at this revision; this file restores its
    # missing Alembic graph entry and must not replay unverified DDL.
    pass


def downgrade() -> None:
    # Preserve the compatibility marker; there is no safe inverse operation.
    pass
