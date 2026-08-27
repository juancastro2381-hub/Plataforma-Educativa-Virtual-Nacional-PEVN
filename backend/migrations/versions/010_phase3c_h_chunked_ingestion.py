"""Phase 3C-H Chunked Ingestion & Forensic Batch Tracking

Revision ID: 010_phase3c_h_chunked_ingestion
Revises: 009_phase3c_f_batch_metrics
Create Date: 2026-08-26 13:30:00.000000

Adds chunked execution tracking and batch audit metrics:
  - official_catalog_sync_batches: failed_chunks, total_chunks, processed_chunks, ingestion_progress, audit_status
  - creates table official_catalog_sync_chunks
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "010_phase3c_h_chunked_ingestion"
down_revision: str | None = "009_phase3c_f_batch_metrics"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add batch chunk tracking columns
    op.add_column(
        "official_catalog_sync_batches",
        sa.Column("failed_chunks", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "official_catalog_sync_batches",
        sa.Column("total_chunks", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "official_catalog_sync_batches",
        sa.Column("processed_chunks", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "official_catalog_sync_batches",
        sa.Column("ingestion_progress", sa.Float(), nullable=False, server_default="100.0"),
    )
    op.add_column(
        "official_catalog_sync_batches",
        sa.Column("audit_status", sa.String(length=50), nullable=False, server_default="VERIFIED"),
    )

    # 2. Create official_catalog_sync_chunks table
    op.create_table(
        "official_catalog_sync_chunks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "batch_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("official_catalog_sync_batches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="PENDING"),
        sa.Column("total_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("valid_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("inserted_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duplicate_records", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_details", sa.Text(), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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

    op.create_index(
        "ix_official_catalog_sync_chunks_batch_id",
        "official_catalog_sync_chunks",
        ["batch_id"],
    )
    op.create_index(
        "ix_official_catalog_sync_chunks_status",
        "official_catalog_sync_chunks",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_official_catalog_sync_chunks_status", table_name="official_catalog_sync_chunks")
    op.drop_index("ix_official_catalog_sync_chunks_batch_id", table_name="official_catalog_sync_chunks")
    op.drop_table("official_catalog_sync_chunks")

    op.drop_column("official_catalog_sync_batches", "audit_status")
    op.drop_column("official_catalog_sync_batches", "ingestion_progress")
    op.drop_column("official_catalog_sync_batches", "processed_chunks")
    op.drop_column("official_catalog_sync_batches", "total_chunks")
    op.drop_column("official_catalog_sync_batches", "failed_chunks")
