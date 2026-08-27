"""Phase 3C National Catalog Promotion Authorization Hardening Schema

Revision ID: 013_phase3c_promotion_auth_hardening
Revises: 012_phase3c_promotion_governance
Create Date: 2026-08-27 03:30:00.000000

Adds cryptographic binding fields and consumption tracking to official_catalog_promotion_authorizations:
  - plan_hash
  - snapshot_id
  - consumed_at
  - consumed_by
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "013_phase3c_promotion_auth_hardening"
down_revision: str | None = "012_phase3c_promotion_governance"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "official_catalog_promotion_authorizations",
        sa.Column("plan_hash", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "official_catalog_promotion_authorizations",
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "official_catalog_promotion_authorizations",
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "official_catalog_promotion_authorizations",
        sa.Column("consumed_by", sa.String(length=100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("official_catalog_promotion_authorizations", "consumed_by")
    op.drop_column("official_catalog_promotion_authorizations", "consumed_at")
    op.drop_column("official_catalog_promotion_authorizations", "snapshot_id")
    op.drop_column("official_catalog_promotion_authorizations", "plan_hash")
