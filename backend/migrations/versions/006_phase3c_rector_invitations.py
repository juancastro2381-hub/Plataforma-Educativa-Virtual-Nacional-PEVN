"""Phase 3C Institutional Provisioning and Rector Invitations

Revision ID: 006_phase3c_rector_invitations
Revises: 005_phase4_virtual_classrooms
Create Date: 2026-08-25 15:30:00.000000

Creates:
  - rector_invitations (Secure single-use tokenized rector onboarding invitations)
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "006_phase3c_rector_invitations"
down_revision: str | None = "005_phase4_virtual_classrooms"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create rector_invitations table
    op.create_table(
        "rector_invitations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "institution_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "token_hash",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "invited_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "is_used",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "used_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "is_revoked",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # 2. Indexes
    op.create_index(
        "ix_rector_invitations_token_hash",
        "rector_invitations",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        "ix_rector_invitations_institution_id",
        "rector_invitations",
        ["institution_id"],
    )
    op.create_index(
        "ix_rector_invitations_user_id",
        "rector_invitations",
        ["user_id"],
    )
    op.create_index(
        "ix_rector_invitations_expires_at",
        "rector_invitations",
        ["expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_rector_invitations_expires_at", table_name="rector_invitations")
    op.drop_index("ix_rector_invitations_user_id", table_name="rector_invitations")
    op.drop_index("ix_rector_invitations_institution_id", table_name="rector_invitations")
    op.drop_index("ix_rector_invitations_token_hash", table_name="rector_invitations")
    op.drop_table("rector_invitations")
