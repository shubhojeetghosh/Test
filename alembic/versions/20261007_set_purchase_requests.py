"""Add student paid-set requests for admin review."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20261007_set_purchase_requests"
down_revision: Union[str, Sequence[str], None] = "a91f2d6c0e43"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "student_set_purchase_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "student_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "exam_set_id",
            sa.Integer(),
            sa.ForeignKey("exam_sets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=20), server_default="PENDING", nullable=False),
        sa.Column("requested_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "handled_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("handled_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint(
            "student_id",
            "exam_set_id",
            name="uq_student_set_purchase_request",
        ),
    )
    op.create_index(
        "ix_student_set_purchase_requests_status_requested_at",
        "student_set_purchase_requests",
        ["status", "requested_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_student_set_purchase_requests_status_requested_at",
        table_name="student_set_purchase_requests",
    )
    op.drop_table("student_set_purchase_requests")
