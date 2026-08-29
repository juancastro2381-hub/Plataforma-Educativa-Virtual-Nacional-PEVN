"""Rector Invitations Audit Timestamps Alignment Schema

Revision ID: 015_rector_invitations_audit_timestamps
Revises: 014_role_permissions_audit_timestamps
Create Date: 2026-08-29 01:30:00.000000

Aligns physical PostgreSQL rector_invitations table with canonical SQLAlchemy RectorInvitation(Base) model:
  - Adds updated_at (TIMESTAMP WITH TIME ZONE, server_default=now(), NOT NULL)
  - Preserves primary key, foreign keys, unique constraints, and indexes.
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "015_rector_invitations_audit_timestamps"
down_revision: str | None = "014_role_permissions_audit_timestamps"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "rector_invitations",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("rector_invitations", "updated_at")
