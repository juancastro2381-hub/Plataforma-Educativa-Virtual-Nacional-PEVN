"""Phase 3C National Catalog Promotion Governance Schema

Revision ID: 012_phase3c_promotion_governance
Revises: 011_phase3c_l_expand_status_lengths
Create Date: 2026-08-27 03:00:00.000000

Creates governance, authorization, snapshot, audit event and concurrency lock tables:
  - official_catalog_promotion_authorizations
  - official_catalog_promotion_snapshots
  - official_catalog_promotion_events
  - official_catalog_promotion_locks
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "012_phase3c_promotion_governance"
down_revision: str | None = "011_phase3c_l_expand_status_lengths"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Authorizations Table
    op.create_table(
        "official_catalog_promotion_authorizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("actor_id", sa.String(length=100), nullable=True),
        sa.Column("actor_email", sa.String(length=255), nullable=False),
        sa.Column("actor_role", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, default="GRANTED", server_default="GRANTED"),
        sa.Column("catalog_status_before", sa.String(length=50), nullable=False),
        sa.Column("catalog_hash", sa.String(length=64), nullable=False),
        sa.Column("preflight_certification_hash", sa.String(length=64), nullable=False),
        sa.Column("decision", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("correlation_id", sa.String(length=100), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 2. Snapshots Table
    op.create_table(
        "official_catalog_promotion_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("authorization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("official_catalog_promotion_authorizations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("snapshot_hash", sa.String(length=64), nullable=False),
        sa.Column("catalog_hash", sa.String(length=64), nullable=False),
        sa.Column("institutions_count", sa.Integer(), nullable=False, default=0),
        sa.Column("campuses_count", sa.Integer(), nullable=False, default=0),
        sa.Column("principal_campuses_count", sa.Integer(), nullable=False, default=0),
        sa.Column("annex_campuses_count", sa.Integer(), nullable=False, default=0),
        sa.Column("departments_count", sa.Integer(), nullable=False, default=0),
        sa.Column("municipalities_count", sa.Integer(), nullable=False, default=0),
        sa.Column("metadata_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 3. Events Table
    op.create_table(
        "official_catalog_promotion_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("correlation_id", sa.String(length=100), nullable=False, index=True),
        sa.Column("actor_id", sa.String(length=100), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=False, index=True),
        sa.Column("state_before", sa.String(length=50), nullable=False),
        sa.Column("state_after", sa.String(length=50), nullable=False),
        sa.Column("catalog_hash", sa.String(length=64), nullable=True),
        sa.Column("result", sa.String(length=30), nullable=False),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 4. Locks Table
    op.create_table(
        "official_catalog_promotion_locks",
        sa.Column("lock_key", sa.String(length=50), primary_key=True),
        sa.Column("acquired_by", sa.String(length=100), nullable=False),
        sa.Column("correlation_id", sa.String(length=100), nullable=False),
        sa.Column("acquired_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("official_catalog_promotion_locks")
    op.drop_table("official_catalog_promotion_events")
    op.drop_table("official_catalog_promotion_snapshots")
    op.drop_table("official_catalog_promotion_authorizations")
