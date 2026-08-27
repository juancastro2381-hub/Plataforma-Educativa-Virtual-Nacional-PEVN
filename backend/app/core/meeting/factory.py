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


_mock_provider_instance: MockMeetingProvider | None = None


def get_meeting_provider(settings: Settings | None = None) -> IMeetingProvider:
    """
    Factory function resolving the active meeting provider.

    :param settings: Optional Settings instance. If None, loads cached settings.
    :return: An object implementing IMeetingProvider.
    """
    global _mock_provider_instance
    active_settings = settings or get_settings()
    provider_type = getattr(active_settings, "MEETING_PROVIDER_TYPE", "mock").lower()

    if provider_type == "bbb":
        return BBBAdapter(
            api_url=active_settings.BBB_API_URL,
            shared_secret=active_settings.BBB_SHARED_SECRET,
            signing_algorithm=getattr(active_settings, "BBB_SIGNING_ALGORITHM", "sha1"),
            timeout_seconds=getattr(active_settings, "BBB_TIMEOUT_SECONDS", 10.0),
        )

    if _mock_provider_instance is None:
        _mock_provider_instance = MockMeetingProvider()
    return _mock_provider_instance


def reset_meeting_provider() -> None:
    """Reset the mock meeting provider singleton state."""
    global _mock_provider_instance
    if _mock_provider_instance is not None:
        _mock_provider_instance.reset()
    _mock_provider_instance = None

