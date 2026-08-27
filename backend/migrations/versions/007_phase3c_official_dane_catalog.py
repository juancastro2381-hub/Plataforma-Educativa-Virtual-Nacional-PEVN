"""Phase 3C Official DANE/MEN Institutional Catalog

Revision ID: 007_phase3c_official_dane_catalog
Revises: 006_phase3c_rector_invitations
Create Date: 2026-08-26 10:00:00.000000

Creates:
  - official_institution_catalog (Authoritative Colombian Educational Establishments registry)
  - official_campus_catalog (Authoritative Colombian Educational Campuses/Sites registry)
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "007_phase3c_official_dane_catalog"
down_revision: str | None = "006_phase3c_rector_invitations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create official_institution_catalog table
    op.create_table(
        "official_institution_catalog",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "dane_code",
            sa.String(length=12),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "department_code",
            sa.String(length=10),
            nullable=False,
        ),
        sa.Column(
            "department_name",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "municipality_code",
            sa.String(length=10),
            nullable=False,
        ),
        sa.Column(
            "municipality_name",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "secretaria_code",
            sa.String(length=50),
            nullable=True,
        ),
        sa.Column(
            "secretaria_name",
            sa.String(length=150),
            nullable=True,
        ),
        sa.Column(
            "sector",
            sa.String(length=50),
            nullable=False,
            server_default="OFICIAL",
        ),
        sa.Column(
            "zone",
            sa.String(length=50),
            nullable=False,
            server_default="URBANA",
        ),
        sa.Column(
            "calendar",
            sa.String(length=20),
            nullable=False,
            server_default="A",
        ),
        sa.Column(
            "academic_character",
            sa.String(length=100),
            nullable=False,
            server_default="ACADÉMICO",
        ),
        sa.Column(
            "official_address",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "official_phone",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "official_email",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "educational_levels",
            sa.String(length=255),
            nullable=True,
            server_default="PREESCOLAR,PRIMARIA,SECUNDARIA,MEDIA",
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="ACTIVO",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "source_system",
            sa.String(length=100),
            nullable=False,
            server_default="MEN_DUE / DANE DIREDU",
        ),
        sa.Column(
            "source_dataset",
            sa.String(length=100),
            nullable=False,
            server_default="datos.gov.co/c36d-tcj8",
        ),
        sa.Column(
            "source_record_id",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "source_updated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
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
        "ix_official_institution_catalog_dane_code",
        "official_institution_catalog",
        ["dane_code"],
        unique=True,
    )
    op.create_index(
        "ix_official_institution_catalog_name",
        "official_institution_catalog",
        ["name"],
    )
    op.create_index(
        "ix_official_institution_catalog_dept_code",
        "official_institution_catalog",
        ["department_code"],
    )
    op.create_index(
        "ix_official_institution_catalog_muni_code",
        "official_institution_catalog",
        ["municipality_code"],
    )

    # 2. Create official_campus_catalog table
    op.create_table(
        "official_campus_catalog",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "official_institution_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("official_institution_catalog.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "dane_sede_code",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "is_main",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "zone",
            sa.String(length=50),
            nullable=True,
            server_default="URBANA",
        ),
        sa.Column(
            "address",
            sa.String(length=255),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="ACTIVA",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
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
        "ix_official_campus_catalog_inst_id",
        "official_campus_catalog",
        ["official_institution_id"],
    )
    op.create_index(
        "ix_official_campus_catalog_dane_sede_code",
        "official_campus_catalog",
        ["dane_sede_code"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_official_campus_catalog_dane_sede_code",
        table_name="official_campus_catalog",
    )
    op.drop_index(
        "ix_official_campus_catalog_inst_id",
        table_name="official_campus_catalog",
    )
    op.drop_table("official_campus_catalog")

    op.drop_index(
        "ix_official_institution_catalog_muni_code",
        table_name="official_institution_catalog",
    )
    op.drop_index(
        "ix_official_institution_catalog_dept_code",
        table_name="official_institution_catalog",
    )
    op.drop_index(
        "ix_official_institution_catalog_name",
        table_name="official_institution_catalog",
    )
    op.drop_index(
        "ix_official_institution_catalog_dane_code",
        table_name="official_institution_catalog",
    )
    op.drop_table("official_institution_catalog")
