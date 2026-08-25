"""
PEVN Backend — Virtual Classroom Pydantic Schemas

Defines request and response schemas for virtual classrooms, session join tokens,
participant attendance, and recording assets.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.virtual_classroom import (
    MeetingParticipantRole,
    VirtualClassroomStatus,
)


class VirtualClassroomCreateRequest(BaseModel):
    """Payload for scheduling/creating a new virtual classroom session."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(
        ...,
        min_length=3,
        max_length=150,
        description="Session title / topic name",
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional session agenda or description",
    )
    academic_assignment_id: uuid.UUID | None = Field(
        default=None,
        description="Optional ID of associated Teacher-Subject-Group assignment",
    )
    scheduled_start_time: datetime | None = Field(
        default=None,
        description="Planned session start timestamp",
    )
    scheduled_end_time: datetime | None = Field(
        default=None,
        description="Planned session conclusion timestamp",
    )
    is_recording_enabled: bool = Field(
        default=True,
        description="Whether cloud recording is activated for this session",
    )
    is_breakout_enabled: bool = Field(
        default=False,
        description="Whether breakout rooms are permitted",
    )
    max_participants: int = Field(
        default=100,
        ge=1,
        le=500,
        description="Maximum concurrent participant capacity",
    )
    provider_metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary domain metadata passed to meeting provider",
    )


class VirtualClassroomResponse(BaseModel):
    """Public representation of a virtual classroom entity."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    academic_assignment_id: uuid.UUID | None
    host_user_id: uuid.UUID
    title: str
    description: str | None
    bbb_meeting_id: str
    status: VirtualClassroomStatus
    scheduled_start_time: datetime | None
    scheduled_end_time: datetime | None
    actual_start_time: datetime | None
    actual_end_time: datetime | None
    is_recording_enabled: bool
    is_breakout_enabled: bool
    max_participants: int
    created_at: datetime
    updated_at: datetime


class VirtualClassroomListResponse(BaseModel):
    """Paginated list of virtual classrooms."""

    items: list[VirtualClassroomResponse]
    total: int
    skip: int
    limit: int


class JoinMeetingResponse(BaseModel):
    """Signed meeting entry details delivered to authenticated frontend client."""

    virtual_classroom_id: uuid.UUID
    join_url: str
    role: MeetingParticipantRole
    meeting_title: str


class MeetingAttendanceResponse(BaseModel):
    """Participant attendance entry for a virtual classroom session."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    virtual_classroom_id: uuid.UUID
    user_id: uuid.UUID
    role: MeetingParticipantRole
    joined_at: datetime
    left_at: datetime | None
    duration_seconds: int | None
    user_full_name: str | None = None
    user_email: str | None = None


class MeetingAttendanceListResponse(BaseModel):
    """List of attendance records for a session."""

    items: list[MeetingAttendanceResponse]
    total: int


class MeetingRecordingResponse(BaseModel):
    """Metadata and playback link for a recorded classroom session."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    virtual_classroom_id: uuid.UUID
    bbb_record_id: str
    playback_url: str
    duration_seconds: int
    file_size_bytes: int | None
    is_published: bool
    recorded_at: datetime
    created_at: datetime


class MeetingRecordingListResponse(BaseModel):
    """List of recording assets for a session."""

    items: list[MeetingRecordingResponse]
    total: int


class PublishRecordingRequest(BaseModel):
    """Payload to toggle recording visibility."""

    model_config = ConfigDict(extra="forbid")

    is_published: bool = Field(
        ...,
        description="True for students, False to restrict to teachers/admins",
    )
