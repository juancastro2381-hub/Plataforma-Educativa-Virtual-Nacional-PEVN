"""Phase 3C Official DANE/MEN Catalog Sync Batches

Revision ID: 008_phase3c_catalog_sync_batches
Revises: 007_phase3c_official_dane_catalog
Create Date: 2026-08-26 10:30:00.000000

Creates:
  - official_catalog_sync_batches (Audit and metric tracking for catalog synchronization runs)
  - Adds sync_batch_id foreign key on official_institution_catalog
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "008_phase3c_catalog_sync_batches"
down_revision: str | None = "007_phase3c_official_dane_catalog"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create official_catalog_sync_batches table
    op.create_table(
        "official_catalog_sync_batches",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "source_system",
            sa.String(length=100),
            nullable=False,
            server_default="MINISTERIO DE EDUCACION NACIONAL (DUE) / DANE",
        ),
        sa.Column(
            "source_dataset",
            sa.String(length=100),
            nullable=False,
            server_default="datos.gov.co/c36d-tcj8",
        ),
        sa.Column(
            "source_version",
            sa.String(length=50),
            nullable=True,
        ),
        sa.Column(
            "source_published_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default="RUNNING",
        ),
        sa.Column(
            "total_records",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "valid_records",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "rejected_records",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "duplicate_records",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "institutions_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "campuses_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "error_summary",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_index(
        "ix_official_catalog_sync_batches_status",
        "official_catalog_sync_batches",
        ["status"],
    )

    # 2. Add sync_batch_id column to official_institution_catalog
    op.add_column(
        "official_institution_catalog",
        sa.Column(
            "sync_batch_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_official_institution_catalog_sync_batch_id",
        "official_institution_catalog",
        "official_catalog_sync_batches",
        ["sync_batch_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_official_institution_catalog_sync_batch_id",
        "official_institution_catalog",
        ["sync_batch_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_official_institution_catalog_sync_batch_id",
        table_name="official_institution_catalog",
    )
    op.drop_constraint(
        "fk_official_institution_catalog_sync_batch_id",
        "official_institution_catalog",
        type_="foreignkey",
    )
    op.drop_column("official_institution_catalog", "sync_batch_id")
    op.drop_index(
        "ix_official_catalog_sync_batches_status",
        table_name="official_catalog_sync_batches",
    )
    op.drop_table("official_catalog_sync_batches")
