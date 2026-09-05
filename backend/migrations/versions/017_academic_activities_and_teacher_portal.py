"""Academic Activities, Grades, Attendance, and Planning Schema (Phase 13D.5)

Revision ID: 017_teacher_portal_schema
Revises: 016_enrollment_transfer_audit_timestamps
Create Date: 2026-08-30 05:15:00.000000

Creates domain tables for the Teacher Portal:
  - academic_activities (Activity / task / quiz creation and publication lifecycle)
  - activity_grades (Student evaluation scores, feedback, and submission tracking)
  - daily_attendances (Student attendance logging per group, date, and subject)
  - academic_plans (Curricular lesson units, competencies, objectives, and evaluation criteria)
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "017_teacher_portal_schema"
down_revision: str | None = "016_enrollment_transfer_audit_timestamps"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create Enums if needed
    activity_type = postgresql.ENUM(
        "TASK", "WORKSHOP", "QUIZ", "EXAM", "PROJECT", "CLASS_ACTIVITY",
        name="activity_type_enum",
        create_type=False,
    )
    activity_type.create(op.get_bind(), checkfirst=True)

    activity_status = postgresql.ENUM(
        "DRAFT", "PUBLISHED", "CLOSED",
        name="activity_status_enum",
        create_type=False,
    )
    activity_status.create(op.get_bind(), checkfirst=True)

    submission_status = postgresql.ENUM(
        "PENDING", "SUBMITTED", "GRADED",
        name="activity_submission_status_enum",
        create_type=False,
    )
    submission_status.create(op.get_bind(), checkfirst=True)

    attendance_status = postgresql.ENUM(
        "PRESENT", "ABSENT", "EXCUSED", "LATE",
        name="daily_attendance_status_enum",
        create_type=False,
    )
    attendance_status.create(op.get_bind(), checkfirst=True)

    plan_status = postgresql.ENUM(
        "DRAFT", "APPROVED", "IN_PROGRESS", "COMPLETED",
        name="academic_plan_status_enum",
        create_type=False,
    )
    plan_status.create(op.get_bind(), checkfirst=True)

    # 2. Table: academic_activities
    op.create_table(
        "academic_activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("academic_assignment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("academic_year_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("activity_type", postgresql.ENUM("TASK", "WORKSHOP", "QUIZ", "EXAM", "PROJECT", "CLASS_ACTIVITY", name="activity_type_enum", create_type=False), nullable=False, server_default="TASK"),
        sa.Column("status", postgresql.ENUM("DRAFT", "PUBLISHED", "CLOSED", name="activity_status_enum", create_type=False), nullable=False, server_default="DRAFT"),
        sa.Column("publication_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_score", sa.Numeric(precision=4, scale=2), server_default="5.00", nullable=False),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("resource_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("max_score > 0", name="ck_academic_activities_max_score_positive"),
        sa.ForeignKeyConstraint(["academic_assignment_id"], ["academic_assignments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_academic_activities_institution_id"), "academic_activities", ["institution_id"], unique=False)
    op.create_index(op.f("ix_academic_activities_teacher_id"), "academic_activities", ["teacher_id"], unique=False)
    op.create_index(op.f("ix_academic_activities_subject_id"), "academic_activities", ["subject_id"], unique=False)
    op.create_index(op.f("ix_academic_activities_group_id"), "academic_activities", ["group_id"], unique=False)
    op.create_index(op.f("ix_academic_activities_academic_year_id"), "academic_activities", ["academic_year_id"], unique=False)
    op.create_index("ix_academic_activities_tenant_teacher", "academic_activities", ["institution_id", "teacher_id"], unique=False)
    op.create_index("ix_academic_activities_group_subject", "academic_activities", ["group_id", "subject_id", "academic_year_id"], unique=False)

    # 3. Table: activity_grades
    op.create_table(
        "activity_grades",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("activity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("score", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("status", postgresql.ENUM("PENDING", "SUBMITTED", "GRADED", name="activity_submission_status_enum", create_type=False), nullable=False, server_default="PENDING"),
        sa.Column("graded_by_teacher_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("graded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("score >= 0", name="ck_activity_grades_score_non_negative"),
        sa.ForeignKeyConstraint(["activity_id"], ["academic_activities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["graded_by_teacher_id"], ["teachers.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("activity_id", "student_id", name="uq_activity_grades_activity_student"),
    )
    op.create_index(op.f("ix_activity_grades_activity_id"), "activity_grades", ["activity_id"], unique=False)
    op.create_index(op.f("ix_activity_grades_student_id"), "activity_grades", ["student_id"], unique=False)

    # 4. Table: daily_attendances
    op.create_table(
        "daily_attendances",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("academic_year_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attendance_date", sa.Date(), nullable=False),
        sa.Column("status", postgresql.ENUM("PRESENT", "ABSENT", "EXCUSED", "LATE", name="daily_attendance_status_enum", create_type=False), nullable=False, server_default="PRESENT"),
        sa.Column("remarks", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_id", "student_id", "attendance_date", "subject_id", name="uq_daily_attendances_session_student"),
    )
    op.create_index(op.f("ix_daily_attendances_institution_id"), "daily_attendances", ["institution_id"], unique=False)
    op.create_index(op.f("ix_daily_attendances_group_id"), "daily_attendances", ["group_id"], unique=False)
    op.create_index(op.f("ix_daily_attendances_student_id"), "daily_attendances", ["student_id"], unique=False)
    op.create_index("ix_daily_attendances_query", "daily_attendances", ["group_id", "attendance_date"], unique=False)

    # 5. Table: academic_plans
    op.create_table(
        "academic_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("academic_assignment_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("academic_year_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("unit_name", sa.String(length=200), nullable=False),
        sa.Column("competencies", sa.Text(), nullable=True),
        sa.Column("learning_objectives", sa.Text(), nullable=True),
        sa.Column("methodology", sa.Text(), nullable=True),
        sa.Column("evaluation_criteria", sa.Text(), nullable=True),
        sa.Column("resources", sa.Text(), nullable=True),
        sa.Column("status", postgresql.ENUM("DRAFT", "APPROVED", "IN_PROGRESS", "COMPLETED", name="academic_plan_status_enum", create_type=False), nullable=False, server_default="DRAFT"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["academic_assignment_id"], ["academic_assignments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_academic_plans_institution_id"), "academic_plans", ["institution_id"], unique=False)
    op.create_index(op.f("ix_academic_plans_teacher_id"), "academic_plans", ["teacher_id"], unique=False)
    op.create_index("ix_academic_plans_tenant_teacher", "academic_plans", ["institution_id", "teacher_id"], unique=False)
    op.create_index("ix_academic_plans_group_subject", "academic_plans", ["group_id", "subject_id", "academic_year_id"], unique=False)


def downgrade() -> None:
    op.drop_table("academic_plans")
    op.drop_table("daily_attendances")
    op.drop_table("activity_grades")
    op.drop_table("academic_activities")

    op.execute("DROP TYPE IF EXISTS academic_plan_status_enum")
    op.execute("DROP TYPE IF EXISTS daily_attendance_status_enum")
    op.execute("DROP TYPE IF EXISTS activity_submission_status_enum")
    op.execute("DROP TYPE IF EXISTS activity_status_enum")
    op.execute("DROP TYPE IF EXISTS activity_type_enum")
