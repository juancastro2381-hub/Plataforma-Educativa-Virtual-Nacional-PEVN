"""Guardian Invitations Table Schema

Revision ID: 020_guardian_invitations
Revises: 019_siee_evaluations_and_promotions
Create Date: 2026-09-06 20:00:00.000000

Creates:
  - guardian_invitations (Secure single-use tokenized guardian onboarding invitations)
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "020_guardian_invitations"
down_revision: str | None = "019_siee_evaluations_and_promotions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create guardian_invitations table
    op.create_table(
        "guardian_invitations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "guardian_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("guardians.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "institution_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("institutions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "token_hash",
            sa.String(length=64),
            nullable=False,
        ),
        sa.Column(
            "email",
            sa.String(length=255),
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
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # 2. Indexes
    op.create_index(
        "ix_guardian_invitations_token_hash",
        "guardian_invitations",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        "ix_guardian_invitations_guardian_id",
        "guardian_invitations",
        ["guardian_id"],
    )
    op.create_index(
        "ix_guardian_invitations_student_id",
        "guardian_invitations",
        ["student_id"],
    )
    op.create_index(
        "ix_guardian_invitations_institution_id",
        "guardian_invitations",
        ["institution_id"],
    )
    op.create_index(
        "ix_guardian_invitations_expires_at",
        "guardian_invitations",
        ["expires_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_guardian_invitations_expires_at", table_name="guardian_invitations")
    op.drop_index("ix_guardian_invitations_institution_id", table_name="guardian_invitations")
    op.drop_index("ix_guardian_invitations_student_id", table_name="guardian_invitations")
    op.drop_index("ix_guardian_invitations_guardian_id", table_name="guardian_invitations")
    op.drop_index("ix_guardian_invitations_token_hash", table_name="guardian_invitations")
    op.drop_table("guardian_invitations")
