"""Phase 4 Virtual Classrooms, Attendance and Recordings (Step 1)

Revision ID: 005_phase4_virtual_classrooms
Revises: 004_phase3_enrollments_assign
Create Date: 2026-08-23 11:00:00.000000

Creates:
  - virtual_classroom_status_enum (SCHEDULED, RUNNING, ENDED, CANCELLED)
  - meeting_participant_role_enum (MODERATOR, VIEWER)
  - virtual_classrooms (Meeting sessions anchored to institutions/academic assignments)
  - meeting_attendances (Participant attendance join/leave logging)
  - meeting_recordings (Session recording archives & playback metadata)
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "005_phase4_virtual_classrooms"
down_revision: str | None = "004_phase3_enrollments_assign"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Enums
    vc_status = postgresql.ENUM(
        "SCHEDULED",
        "RUNNING",
        "ENDED",
        "CANCELLED",
        name="virtual_classroom_status_enum",
        create_type=False,
    )
    vc_status.create(op.get_bind(), checkfirst=True)

    part_role = postgresql.ENUM(
        "MODERATOR",
        "VIEWER",
        name="meeting_participant_role_enum",
        create_type=False,
    )
    part_role.create(op.get_bind(), checkfirst=True)

    # 2. Virtual Classrooms Table
    op.create_table(
        "virtual_classrooms",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "institution_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "academic_assignment_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
        sa.Column(
            "host_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("bbb_meeting_id", sa.String(100), nullable=False),
        sa.Column("moderator_password_hash", sa.String(255), nullable=False),
        sa.Column("attendee_password_hash", sa.String(255), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "SCHEDULED",
                "RUNNING",
                "ENDED",
                "CANCELLED",
                name="virtual_classroom_status_enum",
                create_type=False,
            ),
            server_default="SCHEDULED",
            nullable=False,
        ),
        sa.Column("scheduled_start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "is_recording_enabled",
            sa.Boolean(),
            server_default="true",
            nullable=False,
        ),
        sa.Column(
            "is_breakout_enabled",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
        sa.Column(
            "max_participants",
            sa.Integer(),
            server_default="100",
            nullable=False,
        ),
        sa.Column("provider_metadata", postgresql.JSONB(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["institution_id"],
            ["institutions.id"],
            name="fk_virtual_classrooms_institution_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["academic_assignment_id"],
            ["academic_assignments.id"],
            name="fk_virtual_classrooms_academic_assignment_id",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["host_user_id"],
            ["users.id"],
            name="fk_virtual_classrooms_host_user_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_virtual_classrooms"),
        sa.UniqueConstraint("bbb_meeting_id", name="uq_virtual_classrooms_bbb_id"),
        sa.CheckConstraint(
            "max_participants > 0",
            name="ck_virtual_classrooms_max_participants",
        ),
        sa.CheckConstraint(
            "scheduled_end_time IS NULL OR scheduled_start_time IS NULL OR scheduled_start_time < scheduled_end_time",
            name="ck_virtual_classrooms_scheduled_dates",
        ),
    )

    op.create_index(
        "ix_virtual_classrooms_institution_id",
        "virtual_classrooms",
        ["institution_id"],
    )
    op.create_index(
        "ix_virtual_classrooms_academic_assignment_id",
        "virtual_classrooms",
        ["academic_assignment_id"],
    )
    op.create_index(
        "ix_virtual_classrooms_host_user_id",
        "virtual_classrooms",
        ["host_user_id"],
    )
    op.create_index(
        "ix_virtual_classrooms_inst_status",
        "virtual_classrooms",
        ["institution_id", "status"],
    )
    op.create_index(
        "ix_virtual_classrooms_assign_status",
        "virtual_classrooms",
        ["academic_assignment_id", "status"],
    )
    op.create_index(
        "ix_virtual_classrooms_host_status",
        "virtual_classrooms",
        ["host_user_id", "status"],
    )

    # 3. Meeting Attendances Table
    op.create_table(
        "meeting_attendances",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "virtual_classroom_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "role",
            postgresql.ENUM(
                "MODERATOR",
                "VIEWER",
                name="meeting_participant_role_enum",
                create_type=False,
            ),
            server_default="VIEWER",
            nullable=False,
        ),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("left_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["virtual_classroom_id"],
            ["virtual_classrooms.id"],
            name="fk_meeting_attendances_virtual_classroom_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_meeting_attendances_user_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_meeting_attendances"),
        sa.CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds >= 0",
            name="ck_meeting_attendances_duration",
        ),
    )

    op.create_index(
        "ix_meeting_attendances_virtual_classroom_id",
        "meeting_attendances",
        ["virtual_classroom_id"],
    )
    op.create_index(
        "ix_meeting_attendances_user_id",
        "meeting_attendances",
        ["user_id"],
    )
    op.create_index(
        "ix_meeting_attendances_classroom_user",
        "meeting_attendances",
        ["virtual_classroom_id", "user_id"],
    )

    # 4. Meeting Recordings Table
    op.create_table(
        "meeting_recordings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "institution_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "virtual_classroom_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("bbb_record_id", sa.String(100), nullable=False),
        sa.Column("playback_url", sa.String(500), nullable=False),
        sa.Column(
            "duration_seconds",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column(
            "is_published",
            sa.Boolean(),
            server_default="true",
            nullable=False,
        ),
        sa.Column("recording_metadata", postgresql.JSONB(), nullable=True),
        sa.Column(
            "recorded_at",
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
        sa.ForeignKeyConstraint(
            ["institution_id"],
            ["institutions.id"],
            name="fk_meeting_recordings_institution_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["virtual_classroom_id"],
            ["virtual_classrooms.id"],
            name="fk_meeting_recordings_virtual_classroom_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_meeting_recordings"),
        sa.UniqueConstraint("bbb_record_id", name="uq_meeting_recordings_bbb_id"),
        sa.CheckConstraint(
            "duration_seconds >= 0",
            name="ck_meeting_recordings_duration",
        ),
    )

    op.create_index(
        "ix_meeting_recordings_institution_id",
        "meeting_recordings",
        ["institution_id"],
    )
    op.create_index(
        "ix_meeting_recordings_virtual_classroom_id",
        "meeting_recordings",
        ["virtual_classroom_id"],
    )
    op.create_index(
        "ix_meeting_recordings_classroom_pub",
        "meeting_recordings",
        ["virtual_classroom_id", "is_published"],
    )


def downgrade() -> None:
    # 1. Drop Tables
    op.drop_table("meeting_recordings")
    op.drop_table("meeting_attendances")
    op.drop_table("virtual_classrooms")

    # 2. Drop Enums
    op.execute("DROP TYPE IF EXISTS meeting_participant_role_enum")
    op.execute("DROP TYPE IF EXISTS virtual_classroom_status_enum")
