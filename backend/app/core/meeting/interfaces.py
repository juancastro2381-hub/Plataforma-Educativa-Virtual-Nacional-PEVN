"""
PEVN Backend — Meeting Provider Abstraction & Data Contracts

Defines the domain-neutral protocol and DTOs for virtual classroom meeting providers.
Decouples educational domain logic from third-party videoconferencing implementations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class MeetingCreateOptions:
    """Domain-neutral parameters to provision a new virtual classroom session."""

    meeting_id: str
    title: str
    moderator_password: str
    attendee_password: str
    is_recording_enabled: bool = True
    is_breakout_enabled: bool = False
    max_participants: int = 100
    welcome_message: str | None = None
    logout_url: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class MeetingInfo:
    """Domain-neutral snapshot of a meeting session state on the provider."""

    meeting_id: str
    title: str
    is_running: bool
    participant_count: int = 0
    moderator_count: int = 0
    create_time: int | None = None
    has_been_forcibly_ended: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class JoinMeetingOptions:
    """Domain-neutral parameters to construct a participant join URL."""

    meeting_id: str
    user_name: str
    password: str
    user_id: str
    role: str  # "MODERATOR" or "VIEWER"
    redirect_url: str | None = None


@dataclass(frozen=True)
class EndMeetingOptions:
    """Domain-neutral parameters to terminate an active meeting session."""

    meeting_id: str
    moderator_password: str


@dataclass(frozen=True)
class RecordingInfo:
    """Domain-neutral representation of a recorded session and playback asset."""

    record_id: str
    meeting_id: str
    title: str
    playback_url: str
    duration_seconds: int = 0
    file_size_bytes: int | None = None
    is_published: bool = True
    recorded_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class IMeetingProvider(Protocol):
    """
    Meeting Provider Protocol.

    Abstract interface defining capabilities required by the virtual classroom domain.
    Implementations translate these operations into vendor-specific API calls.
    """

    async def create_meeting(self, options: MeetingCreateOptions) -> MeetingInfo:
        """Provision or register a virtual classroom session."""
        ...

    async def generate_join_url(self, options: JoinMeetingOptions) -> str:
        """Construct a secure, signed participant entry URL."""
        ...

    async def end_meeting(self, options: EndMeetingOptions) -> bool:
        """Terminate an active meeting session on the provider server."""
        ...

    async def is_meeting_running(self, meeting_id: str) -> bool:
        """Check whether a meeting session is currently active/running."""
        ...

    async def get_meeting_info(
        self, meeting_id: str, moderator_password: str
    ) -> MeetingInfo:
        """Fetch real-time session telemetry and participant counts."""
        ...

    async def get_recordings(self, meeting_id: str) -> list[RecordingInfo]:
        """Fetch all recorded assets associated with a meeting identifier."""
        ...
