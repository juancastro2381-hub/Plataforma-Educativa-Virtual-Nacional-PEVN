"""
PEVN Backend — Meeting Provider Factory

Instantiates the configured meeting provider (BigBlueButton or Mock)
based on application settings.
"""

from __future__ import annotations

from app.core.config import Settings, get_settings
from app.core.meeting.bbb_adapter import BBBAdapter
from app.core.meeting.interfaces import IMeetingProvider
from app.core.meeting.mock_provider import MockMeetingProvider


def get_meeting_provider(settings: Settings | None = None) -> IMeetingProvider:
    """
    Factory function resolving the active meeting provider.

    :param settings: Optional Settings instance. If None, loads cached settings.
    :return: An object implementing IMeetingProvider.
    """
    active_settings = settings or get_settings()
    provider_type = getattr(active_settings, "MEETING_PROVIDER_TYPE", "mock").lower()

    if provider_type == "bbb":
        return BBBAdapter(
            api_url=active_settings.BBB_API_URL,
            shared_secret=active_settings.BBB_SHARED_SECRET,
            signing_algorithm=getattr(active_settings, "BBB_SIGNING_ALGORITHM", "sha1"),
            timeout_seconds=getattr(active_settings, "BBB_TIMEOUT_SECONDS", 10.0),
        )

    return MockMeetingProvider()
