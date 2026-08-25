"""Phase 3 Enrollments, Academic Assignments and Integrity Indexes (Step 3)

Revision ID: 004_phase3_enrollments_assign
Revises: 003_phase3_groups_and_actors
Create Date: 2026-08-22 16:00:00.000000

Creates:
  - enrollments (Student enrollment per group and school year with partial unique index)
  - group_transfer_history (Immutable audit trail for group reassignments)
  - academic_assignments (Teacher workload assignment per subject/group with partial unique index)
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "004_phase3_enrollments_assign"
down_revision: str | None = "003_phase3_groups_and_actors"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Enrollment Status Enum
    enrollment_status = postgresql.ENUM(
        "PRE_ENROLLED",
        "ACTIVE",
        "WITHDRAWN",
        "TRANSFERRED",
        "GRADUATED",
        name="enrollment_status_enum",
        create_type=False,
    )
    enrollment_status.create(op.get_bind(), checkfirst=True)

    # 2. Enrollments Table
    op.create_table(
        "enrollments",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("academic_year_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("enrollment_date", sa.Date(), server_default=sa.text("CURRENT_DATE"), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "PRE_ENROLLED",
                "ACTIVE",
                "WITHDRAWN",
                "TRANSFERRED",
                "GRADUATED",
                name="enrollment_status_enum",
                create_type=False,
            ),
            server_default="ACTIVE",
            nullable=False,
        ),
        sa.Column("status_reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_enrollments_academic_year_id"), "enrollments", ["academic_year_id"], unique=False)
    op.create_index(op.f("ix_enrollments_group_id"), "enrollments", ["group_id"], unique=False)
    op.create_index(op.f("ix_enrollments_student_id"), "enrollments", ["student_id"], unique=False)
    op.create_index(
        "ix_enrollments_tenant_query",
        "enrollments",
        ["academic_year_id", "group_id", "status"],
        unique=False,
    )
    # Mandatory Partial Unique Index: Only ONE active enrollment per student/year
    op.create_index(
        "uq_enrollments_single_active_per_year",
        "enrollments",
        ["student_id", "academic_year_id"],
        unique=True,
        postgresql_where=sa.text("status = 'ACTIVE'"),
    )

    # 3. Group Transfer History Table
    op.create_table(
        "group_transfer_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("enrollment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("previous_group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("new_group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("transferred_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("transfer_date", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["enrollment_id"], ["enrollments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["new_group_id"], ["groups.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["previous_group_id"], ["groups.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["transferred_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_group_transfer_history_enrollment_id"), "group_transfer_history", ["enrollment_id"], unique=False)
    op.create_index(op.f("ix_group_transfer_history_new_group_id"), "group_transfer_history", ["new_group_id"], unique=False)
    op.create_index(op.f("ix_group_transfer_history_previous_group_id"), "group_transfer_history", ["previous_group_id"], unique=False)
    op.create_index(op.f("ix_group_transfer_history_transferred_by_user_id"), "group_transfer_history", ["transferred_by_user_id"], unique=False)

    # 4. Academic Assignments Table
    op.create_table(
        "academic_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("group_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("academic_year_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("weekly_hours", sa.SmallInteger(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["subject_id"], ["subjects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("weekly_hours > 0", name="ck_academic_assignments_weekly_hours"),
    )
    op.create_index(op.f("ix_academic_assignments_academic_year_id"), "academic_assignments", ["academic_year_id"], unique=False)
    op.create_index(op.f("ix_academic_assignments_group_id"), "academic_assignments", ["group_id"], unique=False)
    op.create_index(op.f("ix_academic_assignments_subject_id"), "academic_assignments", ["subject_id"], unique=False)
    op.create_index(op.f("ix_academic_assignments_teacher_id"), "academic_assignments", ["teacher_id"], unique=False)
    op.create_index(
        "ix_academic_assignments_lookup",
        "academic_assignments",
        ["teacher_id", "academic_year_id"],
        unique=False,
    )
    # Mandatory Partial Unique Index: Only ONE active teacher assignment per (subject, group, year)
    op.create_index(
        "uq_academic_assignments_single_active",
        "academic_assignments",
        ["subject_id", "group_id", "academic_year_id"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )


def downgrade() -> None:
    op.drop_table("academic_assignments")
    op.drop_table("group_transfer_history")
    op.drop_table("enrollments")
    op.execute("DROP TYPE IF EXISTS enrollment_status_enum;")
