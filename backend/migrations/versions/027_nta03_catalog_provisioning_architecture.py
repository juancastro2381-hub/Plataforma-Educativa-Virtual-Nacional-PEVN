"""Catalog <-> Provisioning Architecture (Phase NTA-03)

Revision ID: 027_nta03_catalog_provisioning_architecture
Revises: 026_nta02_national_divipola_foundation
Create Date: 2026-10-06 06:00:00.000000

Implements Phase NTA-03 of the PEVN National Territorial Architecture:
  - Adds nullable column `catalog_institution_id` (UUID) to `institutions`.
  - Establishes referential integrity via Foreign Key to `official_institution_catalog.id` (ON DELETE SET NULL).
  - Creates lookup index on `institutions.catalog_institution_id`.
  - Creates partial unique index `uq_institutions_catalog_institution_id` enforcing that at most
    one PEVN tenant references any given official catalog record (when NOT NULL).
  - Deterministically backfills `catalog_institution_id` for the 7 verified official PEVN institutions
    matching `official_institution_catalog` by DANE code.
  - Safely maintains `catalog_institution_id = NULL` for the 27 synthetic/test fixture institutions.
  - Safe, non-destructive downgrade strategy.
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "027_nta03_catalog_provisioning_architecture"
down_revision: str | None = "026_nta02_national_divipola_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add catalog_institution_id column to institutions table
    op.add_column(
        "institutions",
        sa.Column(
            "catalog_institution_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    # 2. Create Foreign Key to official_institution_catalog.id (ON DELETE SET NULL)
    op.create_foreign_key(
        "fk_institutions_catalog_institution_id",
        "institutions",
        "official_institution_catalog",
        ["catalog_institution_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # 3. Create regular lookup index on catalog_institution_id
    op.create_index(
        "ix_institutions_catalog_institution_id",
        "institutions",
        ["catalog_institution_id"],
        unique=False,
    )

    # 4. Create partial unique index enforcing 1-to-1 catalog attachment for non-NULL values
    op.create_index(
        "uq_institutions_catalog_institution_id",
        "institutions",
        ["catalog_institution_id"],
        unique=True,
        postgresql_where=sa.text("catalog_institution_id IS NOT NULL"),
    )

    # 5. Deterministic backfill for verified official institutions matching catalog by DANE code
    # (Matches exactly the 7 verified institutions; 27 synthetic test fixtures remain NULL safely)
    backfill_sql = """
    UPDATE institutions i
    SET catalog_institution_id = c.id
    FROM official_institution_catalog c
    WHERE i.dane_code = c.dane_code;
    """
    op.execute(sa.text(backfill_sql))


def downgrade() -> None:
    # 1. Drop partial unique index
    op.drop_index(
        "uq_institutions_catalog_institution_id",
        table_name="institutions",
        postgresql_where=sa.text("catalog_institution_id IS NOT NULL"),
    )

    # 2. Drop lookup index
    op.drop_index(
        "ix_institutions_catalog_institution_id",
        table_name="institutions",
    )

    # 3. Drop Foreign Key constraint
    op.drop_constraint(
        "fk_institutions_catalog_institution_id",
        "institutions",
        type_="foreignkey",
    )

    # 4. Drop catalog_institution_id column
    op.drop_column("institutions", "catalog_institution_id")
