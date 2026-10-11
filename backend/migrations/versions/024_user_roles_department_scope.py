"""User Roles Department Scope Schema (Phase 0.6 Territorial Scope Remediation)

Revision ID: 024_user_roles_department_scope
Revises: 023_student_submissions_and_attachments
Create Date: 2026-10-05 15:00:00.000000

Implements:
  - Add nullable department_id to user_roles table with foreign key to departments.id (ON DELETE CASCADE)
  - Create index ix_user_roles_department_id for high-performance territorial scope resolution
  - Preserve all existing users, roles, superadmin, national_admin, and institutional records
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "024_user_roles_department_scope"
down_revision: str | None = "023_student_submissions_and_attachments"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add department_id column to user_roles
    op.add_column(
        "user_roles",
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("departments.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )

    # 2. Create index on user_roles(department_id)
    op.create_index(
        "ix_user_roles_department_id",
        "user_roles",
        ["department_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_user_roles_department_id", table_name="user_roles")
    op.drop_column("user_roles", "department_id")
