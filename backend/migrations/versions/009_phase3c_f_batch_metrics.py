"""Phase 3C-F Official Catalog Forensic Quality Gates & Metrics

Revision ID: 009_phase3c_f_batch_metrics
Revises: 008_phase3c_catalog_sync_batches
Create Date: 2026-08-26 12:00:00.000000

Adds forensic audit metrics and quality gate columns to official_catalog_sync_batches:
  - departments_count
  - municipalities_count
  - principal_campuses_count
  - annex_campuses_count
  - dataset_checksum
  - quality_gate_status
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "009_phase3c_f_batch_metrics"
down_revision: str | None = "008_phase3c_catalog_sync_batches"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "official_catalog_sync_batches",
        sa.Column("departments_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "official_catalog_sync_batches",
        sa.Column("municipalities_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "official_catalog_sync_batches",
        sa.Column("principal_campuses_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "official_catalog_sync_batches",
        sa.Column("annex_campuses_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "official_catalog_sync_batches",
        sa.Column("dataset_checksum", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "official_catalog_sync_batches",
        sa.Column("quality_gate_status", sa.String(length=50), nullable=True, server_default="PASSED"),
    )


def downgrade() -> None:
    op.drop_column("official_catalog_sync_batches", "quality_gate_status")
    op.drop_column("official_catalog_sync_batches", "dataset_checksum")
    op.drop_column("official_catalog_sync_batches", "annex_campuses_count")
    op.drop_column("official_catalog_sync_batches", "principal_campuses_count")
    op.drop_column("official_catalog_sync_batches", "municipalities_count")
    op.drop_column("official_catalog_sync_batches", "departments_count")
