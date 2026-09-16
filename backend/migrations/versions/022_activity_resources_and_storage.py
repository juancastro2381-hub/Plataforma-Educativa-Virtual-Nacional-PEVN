"""Activity Pedagogical Resources & Secure Storage Schema (Phase B3-H11)

Revision ID: 022_activity_resources_and_storage
Revises: 021_phase15_communications_news_incidents
Create Date: 2026-09-12 10:00:00.000000

Implements the relational table, indices and PostgreSQL ENUM for activity materials:
  - activity_resource_type_enum ('URL', 'FILE')
  - activity_resources table with multi-tenant isolation and foreign key to academic_activities
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "022_activity_resources_and_storage"
down_revision: str | None = "021_phase15_communications_news_incidents"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create Enum
    resource_type = postgresql.ENUM(
        "URL",
        "FILE",
        name="activity_resource_type_enum",
        create_type=False,
    )
    resource_type.create(op.get_bind(), checkfirst=True)

    # 2. Create Table: activity_resources
    op.create_table(
        "activity_resources",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("activity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "resource_type",
            postgresql.ENUM(
                "URL",
                "FILE",
                name="activity_resource_type_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="URL",
        ),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
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
        sa.CheckConstraint(
            "(resource_type = 'URL' AND url IS NOT NULL) OR "
            "(resource_type = 'FILE' AND file_path IS NOT NULL AND original_filename IS NOT NULL)",
            name="ck_activity_resources_type_fields",
        ),
        sa.ForeignKeyConstraint(
            ["activity_id"],
            ["academic_activities.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["institution_id"],
            ["institutions.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_activity_resources_activity_id"),
        "activity_resources",
        ["activity_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_activity_resources_institution_id"),
        "activity_resources",
        ["institution_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_activity_resources_institution_id"), table_name="activity_resources")
    op.drop_index(op.f("ix_activity_resources_activity_id"), table_name="activity_resources")
    op.drop_table("activity_resources")
    op.execute("DROP TYPE IF EXISTS activity_resource_type_enum")
