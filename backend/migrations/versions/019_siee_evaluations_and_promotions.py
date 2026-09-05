"""SIEE Evaluations, Period Grades, Recoveries and Promotions Schema (Phase 16A)

Revision ID: 019_siee_evaluations_and_promotions
Revises: 018_guardian_tenant_isolation
Create Date: 2026-09-01 17:00:00.000000

Implements the institutional SIEE evaluation domain architecture:
  - `performance_level_enum` & `promotion_status_enum` PostgreSQL enums.
  - `siee_policies`: Versioned, institution-configurable SIEE parameters (DECISION-16-01, DECISION-16-02).
  - `period_subject_grades`: Hybrid periodic subject scores (DECISION-16-03).
  - `academic_achievements`: Competency and pedagogical achievement descriptors.
  - `recovery_grades`: Remedial attempts preserving original failing scores with applied cap.
  - `student_promotions`: Year-end academic promotion judgments and commission acts.
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "019_siee_evaluations_and_promotions"
down_revision: str | None = "018_guardian_tenant_isolation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create Enums safely using PostgreSQL IF NOT EXISTS
    conn = op.get_bind()
    
    conn.execute(sa.text("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'performance_level_enum') THEN
                CREATE TYPE performance_level_enum AS ENUM ('BAJO', 'BASICO', 'ALTO', 'SUPERIOR');
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'promotion_status_enum') THEN
                CREATE TYPE promotion_status_enum AS ENUM ('PROMOVIDO', 'NO_PROMOVIDO', 'GRADUADO', 'PENDIENTE_NIVELACION');
            END IF;
        END $$;
    """))

    performance_level_enum = postgresql.ENUM(
        "BAJO",
        "BASICO",
        "ALTO",
        "SUPERIOR",
        name="performance_level_enum",
        create_type=False,
    )

    promotion_status_enum = postgresql.ENUM(
        "PROMOVIDO",
        "NO_PROMOVIDO",
        "GRADUADO",
        "PENDIENTE_NIVELACION",
        name="promotion_status_enum",
        create_type=False,
    )

    # 2. Table: siee_policies
    op.create_table(
        "siee_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("academic_year_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.SmallInteger(), server_default="1", nullable=False),
        sa.Column("name", sa.String(length=150), server_default="Sistema Institucional de Evaluación de los Estudiantes", nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("min_passing_score", sa.Numeric(precision=4, scale=2), server_default="3.00", nullable=False),
        sa.Column("max_score", sa.Numeric(precision=4, scale=2), server_default="5.00", nullable=False),
        sa.Column("low_threshold_max", sa.Numeric(precision=4, scale=2), server_default="2.99", nullable=False),
        sa.Column("basic_threshold_max", sa.Numeric(precision=4, scale=2), server_default="3.99", nullable=False),
        sa.Column("high_threshold_max", sa.Numeric(precision=4, scale=2), server_default="4.59", nullable=False),
        sa.Column("recovery_grade_cap", sa.Numeric(precision=4, scale=2), server_default="3.00", nullable=False),
        sa.Column("max_failed_subjects_for_promotion", sa.SmallInteger(), server_default="2", nullable=False),
        sa.Column("max_failed_core_subjects", sa.SmallInteger(), server_default="1", nullable=False),
        sa.Column("min_attendance_percentage", sa.Numeric(precision=5, scale=2), server_default="75.00", nullable=False),
        sa.Column("attendance_affects_promotion", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("rounding_decimals", sa.SmallInteger(), server_default="1", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("institution_id", "academic_year_id", "version", name="uq_siee_policies_inst_year_version"),
        sa.CheckConstraint("min_passing_score > 0 AND max_score > min_passing_score", name="ck_siee_policies_score_bounds"),
        sa.CheckConstraint("recovery_grade_cap >= min_passing_score AND recovery_grade_cap <= max_score", name="ck_siee_policies_recovery_cap"),
        sa.CheckConstraint("min_attendance_percentage >= 0 AND min_attendance_percentage <= 100", name="ck_siee_policies_attendance_range"),
    )
    op.create_index(
        "uq_siee_policies_one_active_per_year",
        "siee_policies",
        ["institution_id", "academic_year_id"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )

    # 3. Table: period_subject_grades
    op.create_table(
        "period_subject_grades",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("academic_period_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("enrollment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("academic_assignment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("calculated_score", sa.Numeric(precision=4, scale=2), nullable=False),
        sa.Column("final_score", sa.Numeric(precision=4, scale=2), nullable=False),
        sa.Column("adjustment_reason", sa.Text(), nullable=True),
        sa.Column("performance_level", performance_level_enum, server_default="BASICO", nullable=False),
        sa.Column("total_absences", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("unexcused_absences", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("observations", sa.Text(), nullable=True),
        sa.Column("is_locked", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("graded_by_teacher_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("calculated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["academic_assignment_id"], ["academic_assignments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["academic_period_id"], ["academic_periods.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["enrollment_id"], ["enrollments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["graded_by_teacher_id"], ["teachers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("academic_period_id", "student_id", "subject_id", name="uq_period_subject_grades_period_student_subject"),
        sa.CheckConstraint("calculated_score >= 0 AND calculated_score <= 5.0", name="ck_period_grades_calc_bounds"),
        sa.CheckConstraint("final_score >= 0 AND final_score <= 5.0", name="ck_period_grades_final_bounds"),
        sa.CheckConstraint("total_absences >= 0 AND unexcused_absences >= 0 AND unexcused_absences <= total_absences", name="ck_period_grades_absences"),
    )
    op.create_index(
        "ix_period_subject_grades_inst_period_subject",
        "period_subject_grades",
        ["institution_id", "academic_period_id", "subject_id"],
    )
    op.create_index(
        "ix_period_subject_grades_student_period",
        "period_subject_grades",
        ["student_id", "academic_period_id"],
    )

    # 4. Table: academic_achievements
    op.create_table(
        "academic_achievements",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("academic_assignment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("academic_period_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=30), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("performance_level", performance_level_enum, server_default="BASICO", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["academic_assignment_id"], ["academic_assignments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["academic_period_id"], ["academic_periods.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_academic_achievements_assignment_period",
        "academic_achievements",
        ["academic_assignment_id", "academic_period_id"],
    )
    op.create_index(
        "ix_academic_achievements_tenant",
        "academic_achievements",
        ["institution_id"],
    )

    # 5. Table: recovery_grades
    op.create_table(
        "recovery_grades",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("period_subject_grade_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("initial_score", sa.Numeric(precision=4, scale=2), nullable=False),
        sa.Column("recovery_score", sa.Numeric(precision=4, scale=2), nullable=False),
        sa.Column("applied_cap", sa.Numeric(precision=4, scale=2), server_default="3.00", nullable=False),
        sa.Column("final_adjusted_score", sa.Numeric(precision=4, scale=2), nullable=False),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("act_number", sa.String(length=50), nullable=True),
        sa.Column("recovery_date", sa.Date(), nullable=False),
        sa.Column("observations", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["period_subject_grade_id"], ["period_subject_grades.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("initial_score >= 0 AND initial_score <= 5.0", name="ck_recovery_initial_bounds"),
        sa.CheckConstraint("recovery_score >= 0 AND recovery_score <= 5.0", name="ck_recovery_score_bounds"),
        sa.CheckConstraint("final_adjusted_score >= 0 AND final_adjusted_score <= 5.0", name="ck_recovery_adjusted_bounds"),
    )
    op.create_index(
        "ix_recovery_grades_period_grade",
        "recovery_grades",
        ["period_subject_grade_id"],
    )

    # 6. Table: student_promotions
    op.create_table(
        "student_promotions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("academic_year_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cumulative_average", sa.Numeric(precision=4, scale=2), nullable=False),
        sa.Column("failed_subjects_count", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("failed_core_subjects_count", sa.SmallInteger(), server_default="0", nullable=False),
        sa.Column("attendance_percentage", sa.Numeric(precision=5, scale=2), server_default="100.00", nullable=False),
        sa.Column("promotion_status", promotion_status_enum, nullable=False),
        sa.Column("acta_number", sa.String(length=50), nullable=True),
        sa.Column("decision_date", sa.Date(), nullable=False),
        sa.Column("observations", sa.Text(), nullable=True),
        sa.Column("closed_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["closed_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("academic_year_id", "student_id", name="uq_student_promotions_year_student"),
        sa.CheckConstraint("cumulative_average >= 0 AND cumulative_average <= 5.0", name="ck_promotions_avg_bounds"),
        sa.CheckConstraint("failed_subjects_count >= 0 AND failed_core_subjects_count >= 0", name="ck_promotions_failed_bounds"),
        sa.CheckConstraint("attendance_percentage >= 0 AND attendance_percentage <= 100", name="ck_promotions_att_bounds"),
    )
    op.create_index(
        "ix_student_promotions_inst_year_group",
        "student_promotions",
        ["institution_id", "academic_year_id", "group_id"],
    )


def downgrade() -> None:
    op.drop_table("student_promotions")
    op.drop_table("recovery_grades")
    op.drop_table("academic_achievements")
    op.drop_table("period_subject_grades")
    op.drop_table("siee_policies")

    conn = op.get_bind()
    conn.execute(sa.text("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'promotion_status_enum') THEN
                DROP TYPE promotion_status_enum;
            END IF;
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'performance_level_enum') THEN
                DROP TYPE performance_level_enum;
            END IF;
        END $$;
    """))
