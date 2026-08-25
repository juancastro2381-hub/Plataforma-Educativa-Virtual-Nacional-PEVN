"""Phase 3 Groups and Actors Schema (Step 2)

Revision ID: 003_phase3_groups_and_actors
Revises: 002_phase3_academic_foundation
Create Date: 2026-08-22 15:50:00.000000

Creates:
  - teachers (Educator educational profile extending User)
  - groups (Classroom sections per campus, year, grade and shift)
  - students (Student educational profile extending User)
  - guardians (Legal guardians with National ID support)
  - student_guardians (Association between students and guardians)
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003_phase3_groups_and_actors"
down_revision: str | None = "002_phase3_academic_foundation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Enums
    teacher_contract_type = postgresql.ENUM(
        "PROPIEDAD",
        "PROVISIONAL",
        "TEMPORAL",
        name="teacher_contract_type_enum",
        create_type=False,
    )
    teacher_contract_type.create(op.get_bind(), checkfirst=True)

    shift_enum = postgresql.ENUM(
        "MANANA",
        "TARDE",
        "NOCHE",
        "UNICA",
        "SABATINA",
        name="shift_enum",
        create_type=False,
    )
    shift_enum.create(op.get_bind(), checkfirst=True)

    student_gender = postgresql.ENUM(
        "M",
        "F",
        "OTRO",
        name="student_gender_enum",
        create_type=False,
    )
    student_gender.create(op.get_bind(), checkfirst=True)

    guardian_relationship = postgresql.ENUM(
        "PADRE",
        "MADRE",
        "ABUELO_A",
        "TIO_A",
        "TUTOR_LEGAL",
        "OTRO",
        name="guardian_relationship_type_enum",
        create_type=False,
    )
    guardian_relationship.create(op.get_bind(), checkfirst=True)

    # 2. Teachers Table
    op.create_table(
        "teachers",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("specialty_area", sa.String(length=150), nullable=True),
        sa.Column("escalafon_grade", sa.String(length=50), nullable=True),
        sa.Column(
            "contract_type",
            postgresql.ENUM(
                "PROPIEDAD",
                "PROVISIONAL",
                "TEMPORAL",
                name="teacher_contract_type_enum",
                create_type=False,
            ),
            server_default="PROPIEDAD",
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_teachers_user_id"),
    )
    op.create_index(op.f("ix_teachers_institution_id"), "teachers", ["institution_id"], unique=False)
    op.create_index(op.f("ix_teachers_user_id"), "teachers", ["user_id"], unique=True)

    # 3. Groups Table
    op.create_table(
        "groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("campus_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("academic_year_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("grade_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column(
            "shift",
            postgresql.ENUM(
                "MANANA",
                "TARDE",
                "NOCHE",
                "UNICA",
                "SABATINA",
                name="shift_enum",
                create_type=False,
            ),
            server_default="MANANA",
            nullable=False,
        ),
        sa.Column("capacity_limit", sa.SmallInteger(), server_default="40", nullable=False),
        sa.Column("group_director_teacher_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["campus_id"], ["campuses.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["grade_id"], ["grades.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["group_director_teacher_id"], ["teachers.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("campus_id", "academic_year_id", "grade_id", "name", name="uq_groups_campus_year_grade_name"),
        sa.CheckConstraint("capacity_limit > 0", name="ck_groups_capacity_positive"),
    )
    op.create_index(op.f("ix_groups_academic_year_id"), "groups", ["academic_year_id"], unique=False)
    op.create_index(op.f("ix_groups_campus_id"), "groups", ["campus_id"], unique=False)
    op.create_index(op.f("ix_groups_grade_id"), "groups", ["grade_id"], unique=False)
    op.create_index(op.f("ix_groups_group_director_teacher_id"), "groups", ["group_director_teacher_id"], unique=False)

    # 4. Students Table
    op.create_table(
        "students",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code_simat", sa.String(length=50), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=False),
        sa.Column(
            "gender",
            postgresql.ENUM(
                "M",
                "F",
                "OTRO",
                name="student_gender_enum",
                create_type=False,
            ),
            server_default="M",
            nullable=False,
        ),
        sa.Column("blood_type", sa.String(length=5), nullable=True),
        sa.Column("stratum", sa.SmallInteger(), nullable=True),
        sa.Column("eps_health_provider", sa.String(length=100), nullable=True),
        sa.Column("has_disability", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("disability_type", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code_simat", name="uq_students_code_simat"),
        sa.UniqueConstraint("user_id", name="uq_students_user_id"),
        sa.CheckConstraint("stratum IS NULL OR (stratum >= 1 AND stratum <= 6)", name="ck_students_stratum_range"),
    )
    op.create_index(op.f("ix_students_code_simat"), "students", ["code_simat"], unique=True)
    op.create_index(op.f("ix_students_institution_id"), "students", ["institution_id"], unique=False)
    op.create_index(op.f("ix_students_user_id"), "students", ["user_id"], unique=True)

    # 5. Guardians Table
    op.create_table(
        "guardians",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "document_type",
            postgresql.ENUM(
                "CC",
                "TI",
                "CE",
                "PEP",
                "PPT",
                "PASSPORT",
                name="document_type_enum",
                create_type=False,
            ),
            server_default="CC",
            nullable=False,
        ),
        sa.Column("document_number", sa.String(length=50), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column(
            "relationship_type",
            postgresql.ENUM(
                "PADRE",
                "MADRE",
                "ABUELO_A",
                "TIO_A",
                "TUTOR_LEGAL",
                "OTRO",
                name="guardian_relationship_type_enum",
                create_type=False,
            ),
            server_default="MADRE",
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_type", "document_number", name="uq_guardians_document"),
    )
    op.create_index(op.f("ix_guardians_document_number"), "guardians", ["document_number"], unique=False)
    op.create_index(op.f("ix_guardians_user_id"), "guardians", ["user_id"], unique=True)

    # 6. Student-Guardians Association Table
    op.create_table(
        "student_guardians",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("guardian_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "relationship_type",
            postgresql.ENUM(
                "PADRE",
                "MADRE",
                "ABUELO_A",
                "TIO_A",
                "TUTOR_LEGAL",
                "OTRO",
                name="guardian_relationship_type_enum",
                create_type=False,
            ),
            server_default="MADRE",
            nullable=False,
        ),
        sa.Column("is_primary_contact", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("is_authorized_pickup", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["guardian_id"], ["guardians.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("student_id", "guardian_id", name="uq_student_guardians_student_guardian"),
    )
    op.create_index(op.f("ix_student_guardians_guardian_id"), "student_guardians", ["guardian_id"], unique=False)
    op.create_index(op.f("ix_student_guardians_student_id"), "student_guardians", ["student_id"], unique=False)


def downgrade() -> None:
    op.drop_table("student_guardians")
    op.drop_table("guardians")
    op.drop_table("students")
    op.drop_table("groups")
    op.drop_table("teachers")
    op.execute("DROP TYPE IF EXISTS guardian_relationship_type_enum;")
    op.execute("DROP TYPE IF EXISTS student_gender_enum;")
    op.execute("DROP TYPE IF EXISTS shift_enum;")
    op.execute("DROP TYPE IF EXISTS teacher_contract_type_enum;")
