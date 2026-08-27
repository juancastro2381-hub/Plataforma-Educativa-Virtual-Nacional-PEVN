"""Phase 3C-L Expand Quality Gate Status Lengths

Revision ID: 011_phase3c_l_expand_status_lengths
Revises: 010_phase3c_h_chunked_ingestion
Create Date: 2026-08-26 14:38:00.000000

Expands length of status columns on official_catalog_sync_batches:
  - quality_gate_status: VARCHAR(50) -> VARCHAR(255)
  - audit_status: VARCHAR(50) -> VARCHAR(100)
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "011_phase3c_l_expand_status_lengths"
down_revision: str | None = "010_phase3c_h_chunked_ingestion"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "official_catalog_sync_batches",
        "quality_gate_status",
        type_=sa.String(length=255),
        existing_type=sa.String(length=50),
        existing_nullable=False,
        existing_server_default="PASSED",
    )
    op.alter_column(
        "official_catalog_sync_batches",
        "audit_status",
        type_=sa.String(length=100),
        existing_type=sa.String(length=50),
        existing_nullable=False,
        existing_server_default="VERIFIED",
    )


def downgrade() -> None:
    op.alter_column(
        "official_catalog_sync_batches",
        "audit_status",
        type_=sa.String(length=50),
        existing_type=sa.String(length=100),
        existing_nullable=False,
        existing_server_default="VERIFIED",
    )
    op.alter_column(
        "official_catalog_sync_batches",
        "quality_gate_status",
        type_=sa.String(length=50),
        existing_type=sa.String(length=255),
        existing_nullable=False,
        existing_server_default="PASSED",
    )
