"""Department Admin Invitations Schema (Phase 0.6 Secure Invitation & Account Activation)

Revision ID: 025_department_admin_invitations
Revises: 024_user_roles_department_scope
Create Date: 2026-10-05 17:00:00.000000

Implements:
  - Creates department_admin_invitations table mirroring the certified RectorInvitation pattern
  - Persists SHA-256 hash of single-use 48-byte cryptographically secure random token
  - Enforces territorial foreign key to departments.id (ON DELETE CASCADE)
  - Enforces foreign key to users.id (ON DELETE CASCADE)
  - Audit timestamps, expiration tracking, single-use redemption, and revocation flags
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "025_department_admin_invitations"
down_revision: str | None = "024_user_roles_department_scope"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create department_admin_invitations table
    op.create_table(
        "department_admin_invitations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("departments.id", ondelete="CASCADE"),
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
        "ix_department_admin_invitations_token_hash",
        "department_admin_invitations",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        "ix_department_admin_invitations_department_id",
        "department_admin_invitations",
        ["department_id"],
    )
    op.create_index(
        "ix_department_admin_invitations_user_id",
        "department_admin_invitations",
        ["user_id"],
    )
    op.create_index(
        "ix_department_admin_invitations_expires_at",
        "department_admin_invitations",
        ["expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_department_admin_invitations_expires_at", table_name="department_admin_invitations")
    op.drop_index("ix_department_admin_invitations_user_id", table_name="department_admin_invitations")
    op.drop_index("ix_department_admin_invitations_department_id", table_name="department_admin_invitations")
    op.drop_index("ix_department_admin_invitations_token_hash", table_name="department_admin_invitations")
    op.drop_table("department_admin_invitations")
