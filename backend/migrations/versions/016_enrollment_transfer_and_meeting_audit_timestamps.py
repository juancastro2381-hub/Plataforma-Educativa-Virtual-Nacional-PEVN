"""Enrollment Transfer and Meeting Audit Timestamps Alignment Schema

Revision ID: 016_enrollment_transfer_audit_timestamps
Revises: 015_rector_invitations_audit_timestamps
Create Date: 2026-08-30 04:00:00.000000

Aligns physical PostgreSQL tables with canonical SQLAlchemy Base models:
  - group_transfer_history: adds created_at and updated_at (TIMESTAMP WITH TIME ZONE, server_default=now(), NOT NULL)
  - meeting_attendances: adds updated_at (TIMESTAMP WITH TIME ZONE, server_default=now(), NOT NULL)
  - meeting_recordings: adds updated_at (TIMESTAMP WITH TIME ZONE, server_default=now(), NOT NULL)
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "016_enrollment_transfer_audit_timestamps"
down_revision: str | None = "015_rector_invitations_audit_timestamps"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. group_transfer_history table
    op.add_column(
        "group_transfer_history",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "group_transfer_history",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # 2. meeting_attendances table
    op.add_column(
        "meeting_attendances",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # 3. meeting_recordings table
    op.add_column(
        "meeting_recordings",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("meeting_recordings", "updated_at")
    op.drop_column("meeting_attendances", "updated_at")
    op.drop_column("group_transfer_history", "updated_at")
    op.drop_column("group_transfer_history", "created_at")
