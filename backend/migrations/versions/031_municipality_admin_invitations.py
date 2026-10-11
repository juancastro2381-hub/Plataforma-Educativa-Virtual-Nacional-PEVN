"""Municipality Admin Invitations Schema (NTA-09-R2 Secure Invitation & Account Activation)

Revision ID: 031_municipality_admin_invitations
Revises: 030_institution_coordinator_delegation
Create Date: 2026-10-09 04:55:00.000000

Implements:
  - Creates municipality_admin_invitations table mirroring the certified DepartmentAdminInvitation and RectorInvitation patterns
  - Persists SHA-256 hash of single-use 48-byte cryptographically secure random token
  - Enforces territorial foreign key to municipalities.id (ON DELETE CASCADE)
  - Enforces foreign key to users.id (ON DELETE CASCADE)
  - Audit timestamps, expiration tracking, single-use redemption, and revocation flags
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "031_municipality_admin_invitations"
down_revision: str | None = "030_institution_coordinator_delegation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create municipality_admin_invitations table
    op.create_table(
        "municipality_admin_invitations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "municipality_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("municipalities.id", ondelete="CASCADE"),
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
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
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
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # 2. Indexes
    op.create_index(
        "ix_municipality_admin_invitations_token_hash",
        "municipality_admin_invitations",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        "ix_municipality_admin_invitations_municipality_id",
        "municipality_admin_invitations",
        ["municipality_id"],
    )
    op.create_index(
        "ix_municipality_admin_invitations_user_id",
        "municipality_admin_invitations",
        ["user_id"],
    )
    op.create_index(
        "ix_municipality_admin_invitations_expires_at",
        "municipality_admin_invitations",
        ["expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_municipality_admin_invitations_expires_at", table_name="municipality_admin_invitations")
    op.drop_index("ix_municipality_admin_invitations_user_id", table_name="municipality_admin_invitations")
    op.drop_index("ix_municipality_admin_invitations_municipality_id", table_name="municipality_admin_invitations")
    op.drop_index("ix_municipality_admin_invitations_token_hash", table_name="municipality_admin_invitations")
    op.drop_table("municipality_admin_invitations")
