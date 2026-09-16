"""Student Submissions and Attachments Schema (Phase B3-H13)

Revision ID: 023_student_submissions_and_attachments
Revises: 022_activity_resources_and_storage
Create Date: 2026-09-12 12:00:00.000000

Implements:
  - activity_delivery_type_enum ('TEXT', 'FILE', 'TEXT_AND_FILE')
  - submission_status_enum ('DRAFT', 'SUBMITTED', 'LATE', 'RETURNED', 'GRADED')
  - academic_activities.delivery_type column
  - student_submissions table with multi-attempt support and audit timestamps
  - submission_attachments table with secure storage references
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "023_student_submissions_and_attachments"
down_revision: str | None = "022_activity_resources_and_storage"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Create Enums
    delivery_type_enum = postgresql.ENUM(
        "TEXT",
        "FILE",
        "TEXT_AND_FILE",
        name="activity_delivery_type_enum",
        create_type=False,
    )
    delivery_type_enum.create(op.get_bind(), checkfirst=True)

    submission_status_enum = postgresql.ENUM(
        "DRAFT",
        "SUBMITTED",
        "LATE",
        "RETURNED",
        "GRADED",
        name="submission_status_enum",
        create_type=False,
    )
    submission_status_enum.create(op.get_bind(), checkfirst=True)

    # 2. Add delivery_type to academic_activities
    op.add_column(
        "academic_activities",
        sa.Column(
            "delivery_type",
            postgresql.ENUM(
                "TEXT",
                "FILE",
                "TEXT_AND_FILE",
                name="activity_delivery_type_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="FILE",
        ),
    )

    # 3. Create Table: student_submissions
    op.create_table(
        "student_submissions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "institution_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "activity_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("academic_activities.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("students.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "attempt_number",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "DRAFT",
                "SUBMITTED",
                "LATE",
                "RETURNED",
                "GRADED",
                name="submission_status_enum",
                create_type=False,
            ),
            nullable=False,
            server_default="DRAFT",
        ),
        sa.Column(
            "student_response",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "submitted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "is_late",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "return_feedback",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "returned_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "returned_by_teacher_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("teachers.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "activity_id",
            "student_id",
            "attempt_number",
            name="uq_student_submissions_activity_student_attempt",
        ),
    )

    op.create_index(
        "ix_student_submissions_tenant_activity_student",
        "student_submissions",
        ["institution_id", "activity_id", "student_id"],
    )
    op.create_index(
        "ix_student_submissions_activity_status",
        "student_submissions",
        ["activity_id", "status"],
    )

    # 4. Create Table: submission_attachments
    op.create_table(
        "submission_attachments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "institution_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("institutions.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "submission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("student_submissions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "file_path",
            sa.String(length=500),
            nullable=False,
        ),
        sa.Column(
            "original_filename",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "file_size_bytes",
            sa.BigInteger(),
            nullable=False,
        ),
        sa.Column(
            "mime_type",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    op.create_index(
        "ix_submission_attachments_tenant_submission",
        "submission_attachments",
        ["institution_id", "submission_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_submission_attachments_tenant_submission", table_name="submission_attachments")
    op.drop_table("submission_attachments")

    op.drop_index("ix_student_submissions_activity_status", table_name="student_submissions")
    op.drop_index("ix_student_submissions_tenant_activity_student", table_name="student_submissions")
    op.drop_table("student_submissions")

    op.drop_column("academic_activities", "delivery_type")

    op.execute("DROP TYPE IF EXISTS submission_status_enum")
    op.execute("DROP TYPE IF EXISTS activity_delivery_type_enum")
