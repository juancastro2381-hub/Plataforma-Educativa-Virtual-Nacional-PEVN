"""Technical Support Cases and Schema Indexes Alignment

Revision ID: 034_technical_support_cases_and_missing_indexes
Revises: 033_siee_evaluations_audit_timestamps
Create Date: 2026-11-01 19:50:00.000000

Creates the technical_support_cases table if not already created,
and aligns database indexes with SQLAlchemy Base models.
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = "034_technical_support_cases_and_missing_indexes"
down_revision: str | None = "033_siee_evaluations_audit_timestamps"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    existing_tables = set(inspector.get_table_names())

    # 1. Create technical_support_cases table if not exists
    if "technical_support_cases" not in existing_tables:
        op.create_table(
            "technical_support_cases",
            sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("ticket_number", sa.String(32), nullable=False, unique=True),
            sa.Column("title", sa.String(200), nullable=False),
            sa.Column("category", sa.String(50), nullable=False, server_default="SYSTEM"),
            sa.Column("severity", sa.String(20), nullable=False, server_default="MEDIUM"),
            sa.Column("status", sa.String(20), nullable=False, server_default="OPEN"),
            sa.Column("affected_service", sa.String(50), nullable=False, server_default="platform"),
            sa.Column("institution_id", UUID(as_uuid=True), sa.ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True),
            sa.Column("reporter_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("assigned_operator", sa.String(100), nullable=True),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("technical_context", JSONB(), nullable=True),
            sa.Column("resolution_notes", sa.Text(), nullable=True),
            sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )

    # 2. Add indexes safely with if_not_exists inspection
    def safe_create_index(index_name: str, table_name: str, columns: list[str], unique: bool = False) -> None:
        if table_name in existing_tables or table_name == "technical_support_cases":
            try:
                table_indexes = {idx["name"] for idx in inspector.get_indexes(table_name)}
                if index_name not in table_indexes:
                    op.create_index(index_name, table_name, columns, unique=unique)
            except Exception:
                pass

    safe_create_index("ix_technical_support_cases_ticket_number", "technical_support_cases", ["ticket_number"], unique=True)
    safe_create_index("ix_technical_support_cases_category", "technical_support_cases", ["category"])
    safe_create_index("ix_technical_support_cases_severity", "technical_support_cases", ["severity"])
    safe_create_index("ix_technical_support_cases_status", "technical_support_cases", ["status"])
    safe_create_index("ix_technical_support_cases_institution_id", "technical_support_cases", ["institution_id"])
    safe_create_index("ix_technical_support_cases_reporter_id", "technical_support_cases", ["reporter_id"])
    safe_create_index("ix_technical_support_cases_inst_status", "technical_support_cases", ["institution_id", "status"])

    safe_create_index("ix_user_roles_campus_id", "user_roles", ["campus_id"])
    safe_create_index("ix_user_roles_role_id", "user_roles", ["role_id"])
    safe_create_index("ix_virtual_classrooms_bbb_meeting_id", "virtual_classrooms", ["bbb_meeting_id"], unique=True)
    safe_create_index("ix_student_promotions_academic_year_id", "student_promotions", ["academic_year_id"])
    safe_create_index("ix_student_promotions_group_id", "student_promotions", ["group_id"])
    safe_create_index("ix_student_promotions_institution_id", "student_promotions", ["institution_id"])
    safe_create_index("ix_student_promotions_student_id", "student_promotions", ["student_id"])


def downgrade() -> None:
    pass

