"""Institution Coordinator Delegation Setting (NTA-08B Addendum)

Revision ID: 030_institution_coordinator_delegation
Revises: 029_user_roles_municipality_scope
Create Date: 2026-10-09 00:00:00.000000

Implements:
  - Add coordinator_delegation_enabled column to institutions table (Boolean, default False, server_default false, nullable False)
  - Rector-controlled feature flag per institution
  - Default to disabled (false) for safe migration of existing institutions and newly provisioned institutions
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "030_institution_coordinator_delegation"
down_revision: str | None = "029_user_roles_municipality_scope"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "institutions",
        sa.Column(
            "coordinator_delegation_enabled",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("institutions", "coordinator_delegation_enabled")
