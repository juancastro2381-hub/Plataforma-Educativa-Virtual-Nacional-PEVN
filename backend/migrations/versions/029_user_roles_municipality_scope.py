"""User Roles Municipality Scope Schema (NTA-07 Canonical Role Implementation)

Revision ID: 029_user_roles_municipality_scope
Revises: 028_nta04_national_provisioning_workflow
Create Date: 2026-10-08 12:00:00.000000

Implements:
  - Add nullable municipality_id to user_roles table with foreign key to municipalities.id (ON DELETE CASCADE)
  - Create index ix_user_roles_municipality_id for high-performance territorial scope resolution
  - Preserve all existing users, roles, superadmin, national_admin, department_admin, and institutional records
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "029_user_roles_municipality_scope"
down_revision: str | None = "028_nta04_national_provisioning_workflow"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add municipality_id column to user_roles
    op.add_column(
        "user_roles",
        sa.Column(
            "municipality_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("municipalities.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )

    # 2. Create index on user_roles(municipality_id)
    op.create_index(
        "ix_user_roles_municipality_id",
        "user_roles",
        ["municipality_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_user_roles_municipality_id", table_name="user_roles")
    op.drop_column("user_roles", "municipality_id")
