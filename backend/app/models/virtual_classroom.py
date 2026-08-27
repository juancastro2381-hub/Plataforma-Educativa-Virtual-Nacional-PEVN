"""
PEVN Backend — Virtual Classroom & Meeting Domain Models

Domain models for virtual classrooms, real-time meeting sessions,
participant attendance logs, and recorded lecture archives.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.academic_assignment import AcademicAssignment
    from app.models.institution import Institution
    from app.models.user import User


class VirtualClassroomStatus(StrEnum):
    """Lifecycle states of a virtual classroom session."""

    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    ENDED = "ENDED"
    CANCELLED = "CANCELLED"


class MeetingParticipantRole(StrEnum):
    """Participant role in a meeting session."""

    MODERATOR = "MODERATOR"
    VIEWER = "VIEWER"


class VirtualClassroom(Base):
    """
    Virtual Classroom / Meeting Session Entity.

    Anchored to an institution and optionally to an academic assignment
    (Teacher + Subject + Group), or hosted as an institutional session.
    """

    __tablename__ = "virtual_classrooms"
    __table_args__ = (
        Index(
            "ix_virtual_classrooms_inst_status",
            "institution_id",
            "status",
        ),
        Index(
            "ix_virtual_classrooms_assign_status",
            "academic_assignment_id",
            "status",
        ),
        Index(
            "ix_virtual_classrooms_host_status",
            "host_user_id",
            "status",
        ),
        CheckConstraint(
            "max_participants > 0",
            name="ck_virtual_classrooms_max_participants",
        ),
        CheckConstraint(
            "scheduled_end_time IS NULL OR scheduled_start_time IS NULL "
            "OR scheduled_start_time < scheduled_end_time",
            name="ck_virtual_classrooms_scheduled_dates",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant boundary institution.",
    )
    academic_assignment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_assignments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Associated academic assignment, or NULL for institutional rooms.",
    )
    host_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Host/moderator user.",
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Classroom/session title.",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Optional description/agenda for the session.",
    )
    bbb_meeting_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique external meeting identifier for the BigBlueButton provider.",
    )
    moderator_password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Hashed or tokenized moderator password for session entry.",
    )
    attendee_password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Hashed or tokenized attendee password for session entry.",
    )
    status: Mapped[VirtualClassroomStatus] = mapped_column(
        SAEnum(
            VirtualClassroomStatus,
            name="virtual_classroom_status_enum",
            values_callable=lambda e: [item.value for item in e],
        ),
        nullable=False,
        default=VirtualClassroomStatus.SCHEDULED,
        server_default=VirtualClassroomStatus.SCHEDULED.value,
        doc="Current lifecycle status of the virtual classroom.",
    )
    scheduled_start_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Scheduled start time for planned sessions.",
    )
    scheduled_end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Scheduled end time for planned sessions.",
    )
    actual_start_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when the session was actually launched.",
    )
    actual_end_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when the session was formally terminated.",
    )
    is_recording_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
        doc="Whether session recording is enabled in the provider.",
    )
    is_breakout_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
        doc="Whether breakout room functionality is enabled.",
    )
    max_participants: Mapped[int] = mapped_column(
        Integer,
        default=100,
        server_default="100",
        nullable=False,
        doc="Maximum concurrent participant limit for the session.",
    )
    provider_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=True,
        doc="Provider-specific configuration and runtime metadata.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=datetime.now,
        nullable=False,
    )

    # Relationships
    institution: Mapped[Institution] = relationship(
        "Institution",
        lazy="selectin",
    )
    academic_assignment: Mapped[AcademicAssignment | None] = relationship(
        "AcademicAssignment",
        lazy="selectin",
    )
    host_user: Mapped[User] = relationship(
        "User",
        lazy="selectin",
        foreign_keys=[host_user_id],
    )
    attendances: Mapped[list[MeetingAttendance]] = relationship(
        "MeetingAttendance",
        back_populates="virtual_classroom",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    recordings: Mapped[list[MeetingRecording]] = relationship(
        "MeetingRecording",
        back_populates="virtual_classroom",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<VirtualClassroom id={self.id} title='{self.title}' "
            f"status={self.status} bbb_meeting_id='{self.bbb_meeting_id}'>"
        )


class MeetingAttendance(Base):
    """
    Meeting Attendance Entity.

    Logs participant join and leave events, computing active session duration.
    """

    __tablename__ = "meeting_attendances"
    __table_args__ = (
        Index(
            "ix_meeting_attendances_classroom_user",
            "virtual_classroom_id",
            "user_id",
        ),
        CheckConstraint(
            "duration_seconds IS NULL OR duration_seconds >= 0",
            name="ck_meeting_attendances_duration",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    virtual_classroom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("virtual_classrooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Associated virtual classroom session.",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Attending user.",
    )
    role: Mapped[MeetingParticipantRole] = mapped_column(
        SAEnum(
            MeetingParticipantRole,
            name="meeting_participant_role_enum",
            values_callable=lambda e: [item.value for item in e],
        ),
        nullable=False,
        default=MeetingParticipantRole.VIEWER,
        server_default=MeetingParticipantRole.VIEWER.value,
        doc="Role assumed by participant during the meeting.",
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when the user joined the session.",
    )
    left_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when the user disconnected or left the session.",
    )
    duration_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Total active session duration in seconds.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    virtual_classroom: Mapped[VirtualClassroom] = relationship(
        "VirtualClassroom",
        back_populates="attendances",
    )
    user: Mapped[User] = relationship(
        "User",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<MeetingAttendance id={self.id} classroom_id={self.virtual_classroom_id} "
            f"user_id={self.user_id} role={self.role}>"
        )


class MeetingRecording(Base):
    """
    Meeting Recording Entity.

    Represents recorded session metadata and playback URL synchronized from provider.
    """

    __tablename__ = "meeting_recordings"
    __table_args__ = (
        Index(
            "ix_meeting_recordings_classroom_pub",
            "virtual_classroom_id",
            "is_published",
        ),
        CheckConstraint(
            "duration_seconds >= 0",
            name="ck_meeting_recordings_duration",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Tenant boundary institution.",
    )
    virtual_classroom_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("virtual_classrooms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Associated virtual classroom session.",
    )
    bbb_record_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique recording identifier assigned by BigBlueButton.",
    )
    playback_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Secure playback URL for the recorded session.",
    )
    duration_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
        doc="Total recording duration in seconds.",
    )
    file_size_bytes: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
        doc="Total file size of recording assets in bytes.",
    )
    is_published: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
        doc="Whether this recording is published and visible to students.",
    )
    recording_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=True,
        doc="Provider-specific recording formats, thumbnails, and caption metadata.",
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when recording was captured.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    institution: Mapped[Institution] = relationship(
        "Institution",
        lazy="selectin",
    )
    virtual_classroom: Mapped[VirtualClassroom] = relationship(
        "VirtualClassroom",
        back_populates="recordings",
    )

    def __repr__(self) -> str:
        return (
            f"<MeetingRecording id={self.id} classroom_id={self.virtual_classroom_id} "
            f"bbb_record_id='{self.bbb_record_id}' is_published={self.is_published}>"
        )
