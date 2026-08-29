"""Role Permissions Audit Timestamps Alignment Schema

Revision ID: 014_role_permissions_audit_timestamps
Revises: 013_phase3c_promotion_auth_hardening
Create Date: 2026-08-28 04:35:00.000000

Aligns physical PostgreSQL role_permissions table with canonical SQLAlchemy RolePermission(Base) model:
  - Adds created_at (TIMESTAMP WITH TIME ZONE, server_default=now(), NOT NULL)
  - Adds updated_at (TIMESTAMP WITH TIME ZONE, server_default=now(), NOT NULL)
  - Preserves composite primary key (role_id, permission_id) and foreign key cascades.
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "014_role_permissions_audit_timestamps"
down_revision: str | None = "013_phase3c_promotion_auth_hardening"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "role_permissions",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column(
        "role_permissions",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("role_permissions", "updated_at")
    op.drop_column("role_permissions", "created_at")
