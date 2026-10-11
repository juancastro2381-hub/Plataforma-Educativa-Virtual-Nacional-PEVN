"""Coordinator Invitations Schema (NTA-10-R9 Secure Coordinator Invitation & Provisioning)

Revision ID: 032_coordinator_invitations
Revises: 031_municipality_admin_invitations
Create Date: 2026-10-10 20:25:00.000000

Implements:
  - Creates coordinator_invitations table mirroring the certified RectorInvitation, DepartmentAdminInvitation, and MunicipalityAdminInvitation patterns
  - Persists SHA-256 hash of single-use 48-byte cryptographically secure random token
  - Enforces institutional foreign key to institutions.id (ON DELETE CASCADE)
  - Supports optional campus foreign key to campuses.id (ON DELETE SET NULL)
  - Enforces foreign key to users.id (ON DELETE CASCADE)
  - Audit timestamps, expiration tracking, single-use redemption, and revocation flags
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "032_coordinator_invitations"
down_revision: str | None = "031_municipality_admin_invitations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create coordinator_invitations table
    op.create_table(
        "coordinator_invitations",
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
            "campus_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("campuses.id", ondelete="SET NULL"),
            nullable=True,
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
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "used_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "is_revoked",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # 2. Indexes
    op.create_index(
        "ix_coordinator_invitations_token_hash",
        "coordinator_invitations",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        "ix_coordinator_invitations_institution_id",
        "coordinator_invitations",
        ["institution_id"],
        unique=False,
    )
    op.create_index(
        "ix_coordinator_invitations_campus_id",
        "coordinator_invitations",
        ["campus_id"],
        unique=False,
    )
    op.create_index(
        "ix_coordinator_invitations_user_id",
        "coordinator_invitations",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_coordinator_invitations_invited_by_id",
        "coordinator_invitations",
        ["invited_by_id"],
        unique=False,
    )
    op.create_index(
        "ix_coordinator_invitations_expires_at",
        "coordinator_invitations",
        ["expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_coordinator_invitations_expires_at", table_name="coordinator_invitations")
    op.drop_index("ix_coordinator_invitations_invited_by_id", table_name="coordinator_invitations")
    op.drop_index("ix_coordinator_invitations_user_id", table_name="coordinator_invitations")
    op.drop_index("ix_coordinator_invitations_campus_id", table_name="coordinator_invitations")
    op.drop_index("ix_coordinator_invitations_institution_id", table_name="coordinator_invitations")
    op.drop_index("ix_coordinator_invitations_token_hash", table_name="coordinator_invitations")
    op.drop_table("coordinator_invitations")
