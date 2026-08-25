"""Phase 3 Academic Foundation Schema (Step 1)

Revision ID: 002_phase3_academic_foundation
Revises: 001_phase2_auth_schema
Create Date: 2026-08-22 15:40:00.000000

Creates:
  - academic_years (Institutional school years)
  - academic_periods (Term evaluation subdivisions)
  - grades (National standardized curriculum levels)
  - knowledge_areas (Curricular areas from Ley 115)
  - subjects (Institution-specific subjects by grade and area)
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_phase3_academic_foundation"
down_revision: str | None = "001_phase2_auth_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Enums
    academic_calendar_type = postgresql.ENUM(
        "CALENDAR_A",
        "CALENDAR_B",
        name="academic_calendar_type_enum",
        create_type=False,
    )
    academic_calendar_type.create(op.get_bind(), checkfirst=True)

    academic_year_status = postgresql.ENUM(
        "PLANNING",
        "ACTIVE",
        "CLOSED",
        "ARCHIVED",
        name="academic_year_status_enum",
        create_type=False,
    )
    academic_year_status.create(op.get_bind(), checkfirst=True)

    educational_level = postgresql.ENUM(
        "PREESCOLAR",
        "PRIMARIA",
        "SECUNDARIA",
        "MEDIA",
        name="educational_level_enum",
        create_type=False,
    )
    educational_level.create(op.get_bind(), checkfirst=True)

    # 2. Grades Table (Shared National Catalog - NO institution_id)
    op.create_table(
        "grades",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "level",
            postgresql.ENUM(
                "PREESCOLAR",
                "PRIMARIA",
                "SECUNDARIA",
                "MEDIA",
                name="educational_level_enum",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("ordinal_order", sa.SmallInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_grades_code"),
    )
    op.create_index(op.f("ix_grades_code"), "grades", ["code"], unique=True)

    # 3. Academic Years Table
    op.create_table(
        "academic_years",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("year", sa.SmallInteger(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "calendar_type",
            postgresql.ENUM(
                "CALENDAR_A",
                "CALENDAR_B",
                name="academic_calendar_type_enum",
                create_type=False,
            ),
            server_default="CALENDAR_A",
            nullable=False,
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "PLANNING",
                "ACTIVE",
                "CLOSED",
                "ARCHIVED",
                name="academic_year_status_enum",
                create_type=False,
            ),
            server_default="PLANNING",
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("institution_id", "year", name="uq_academic_years_institution_year"),
        sa.CheckConstraint("start_date < end_date", name="ck_academic_years_date_order"),
    )
    op.create_index(op.f("ix_academic_years_institution_id"), "academic_years", ["institution_id"], unique=False)
    op.create_index(
        "ix_academic_years_institution_status",
        "academic_years",
        ["institution_id", "status"],
        unique=False,
    )

    # 4. Academic Periods Table
    op.create_table(
        "academic_periods",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("academic_year_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("period_number", sa.SmallInteger(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("weight_percentage", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("is_closed", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("academic_year_id", "period_number", name="uq_academic_periods_year_number"),
        sa.CheckConstraint("weight_percentage > 0 AND weight_percentage <= 100", name="ck_academic_periods_weight"),
        sa.CheckConstraint("start_date < end_date", name="ck_academic_periods_date_order"),
    )
    op.create_index(op.f("ix_academic_periods_academic_year_id"), "academic_periods", ["academic_year_id"], unique=False)

    # 5. Knowledge Areas Table
    op.create_table(
        "knowledge_areas",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("is_mandatory", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_knowledge_areas_institution_id"), "knowledge_areas", ["institution_id"], unique=False)

    # 6. Subjects Table
    op.create_table(
        "subjects",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("knowledge_area_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("grade_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("weekly_hours", sa.SmallInteger(), server_default="4", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["grade_id"], ["grades.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["knowledge_area_id"], ["knowledge_areas.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("institution_id", "grade_id", "name", name="uq_subjects_institution_grade_name"),
        sa.CheckConstraint("weekly_hours > 0", name="ck_subjects_weekly_hours"),
    )
    op.create_index(op.f("ix_subjects_grade_id"), "subjects", ["grade_id"], unique=False)
    op.create_index(op.f("ix_subjects_institution_id"), "subjects", ["institution_id"], unique=False)
    op.create_index(op.f("ix_subjects_knowledge_area_id"), "subjects", ["knowledge_area_id"], unique=False)

    # 7. Seed National Grades Catalog
    national_grades = [
        ("TRANSICION", "Transición", "PREESCOLAR", 0),
        ("G01", "Primero", "PRIMARIA", 1),
        ("G02", "Segundo", "PRIMARIA", 2),
        ("G03", "Tercero", "PRIMARIA", 3),
        ("G04", "Cuarto", "PRIMARIA", 4),
        ("G05", "Quinto", "PRIMARIA", 5),
        ("G06", "Sexto", "SECUNDARIA", 6),
        ("G07", "Séptimo", "SECUNDARIA", 7),
        ("G08", "Octavo", "SECUNDARIA", 8),
        ("G09", "Noveno", "SECUNDARIA", 9),
        ("G10", "Décimo", "MEDIA", 10),
        ("G11", "Undécimo", "MEDIA", 11),
    ]
    for code, name, level, order in national_grades:
        op.execute(
            sa.text(
                "INSERT INTO grades (id, code, name, level, ordinal_order, created_at, updated_at) "
                "VALUES (gen_random_uuid(), :code, :name, CAST(:level AS educational_level_enum), :order, now(), now()) "
                "ON CONFLICT (code) DO NOTHING;"
            ).bindparams(code=code, name=name, level=level, order=order)
        )

    # 8. Seed Standard Statutory MEN Knowledge Areas (institution_id = NULL)
    national_areas = [
        "Ciencias Naturales y Educación Ambiental",
        "Ciencias Sociales, Historia, Geografía y Democracia",
        "Educación Artística y Cultural",
        "Educación Ética y en Valores Humanos",
        "Educación Física, Recreación y Deportes",
        "Educación Religiosa",
        "Humanidades, Lengua Castellana e Idiomas Extranjeros",
        "Matemáticas",
        "Tecnología e Informática",
    ]
    for area_name in national_areas:
        op.execute(
            sa.text(
                "INSERT INTO knowledge_areas (id, institution_id, name, is_mandatory, created_at, updated_at) "
                "VALUES (gen_random_uuid(), NULL, :name, true, now(), now());"
            ).bindparams(name=area_name)
        )


def downgrade() -> None:
    op.drop_table("subjects")
    op.drop_table("knowledge_areas")
    op.drop_table("academic_periods")
    op.drop_table("academic_years")
    op.drop_table("grades")
    op.execute("DROP TYPE IF EXISTS educational_level_enum;")
    op.execute("DROP TYPE IF EXISTS academic_year_status_enum;")
    op.execute("DROP TYPE IF EXISTS academic_calendar_type_enum;")
