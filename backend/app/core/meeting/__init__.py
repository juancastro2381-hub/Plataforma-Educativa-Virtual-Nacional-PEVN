"""
PEVN Backend — Meeting Provider Package

Provides decoupled virtual classroom meeting provider abstractions,
concrete adapters (BigBlueButton), and testing mock providers.
"""

from __future__ import annotations

from app.core.meeting.bbb_adapter import BBBAdapter
from app.core.meeting.exceptions import (
    MeetingNotFoundError,
    MeetingProviderAuthError,
    MeetingProviderConfigError,
    MeetingProviderConnectionError,
    MeetingProviderError,
    MeetingProviderResponseError,
)
from app.core.meeting.factory import get_meeting_provider
from app.core.meeting.interfaces import (
    EndMeetingOptions,
    IMeetingProvider,
    JoinMeetingOptions,
    MeetingCreateOptions,
    MeetingInfo,
    RecordingInfo,
)
from app.core.meeting.mock_provider import MockMeetingProvider

__all__ = [
    "BBBAdapter",
    "EndMeetingOptions",
    "IMeetingProvider",
    "JoinMeetingOptions",
    "MeetingCreateOptions",
    "MeetingInfo",
    "MeetingNotFoundError",
    "MeetingProviderAuthError",
    "MeetingProviderConfigError",
    "MeetingProviderConnectionError",
    "MeetingProviderError",
    "MeetingProviderResponseError",
    "MockMeetingProvider",
    "RecordingInfo",
    "get_meeting_provider",
]
