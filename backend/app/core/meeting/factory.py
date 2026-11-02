"""
PEVN Backend — Meeting Provider Factory

Instantiates the configured meeting provider (BigBlueButton or Mock)
based on application settings.
"""

from __future__ import annotations

from enum import Enum

from app.core.config import Settings, get_settings
from app.core.meeting.bbb_adapter import BBBAdapter
from app.core.meeting.interfaces import IMeetingProvider
from app.core.meeting.mock_provider import MockMeetingProvider


class MeetingProviderStatus(str, Enum):
    """Operational status of the videoconferencing infrastructure."""

    CONFIGURED = "CONFIGURED"
    AVAILABLE = "AVAILABLE"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    TEMPORARILY_UNAVAILABLE = "TEMPORARILY_UNAVAILABLE"
    AUTH_ERROR = "AUTH_ERROR"


def check_meeting_provider_status(
    settings: Settings | None = None,
) -> tuple[MeetingProviderStatus, str]:
    """
    Centralized check distinguishing provider readiness states:
    - CONFIGURED / AVAILABLE: Ready to conduct video conferences.
    - NOT_CONFIGURED: Missing BigBlueButton credentials/commissioning.
    - TEMPORARILY_UNAVAILABLE: Configured but offline or timing out.
    - AUTH_ERROR: Cryptographic salt or authentication failure.
    """
    active_settings = settings or get_settings()
    provider_type = getattr(active_settings, "MEETING_PROVIDER_TYPE", "mock").lower()

    if provider_type == "bbb":
        api_url = getattr(active_settings, "BBB_API_URL", "")
        secret = getattr(active_settings, "BBB_SHARED_SECRET", "")
        if not secret or not secret.strip() or not api_url or not api_url.strip():
            return (
                MeetingProviderStatus.NOT_CONFIGURED,
                "Servicio de videoconferencias pendiente de habilitación. "
                "La infraestructura BigBlueButton aún no ha sido comisionada.",
            )
        return (
            MeetingProviderStatus.CONFIGURED,
            "Servicio BigBlueButton configurado.",
        )

    if provider_type in ("none", "disabled", "unconfigured"):
        return (
            MeetingProviderStatus.NOT_CONFIGURED,
            "Servicio de videoconferencias deshabilitado en este entorno.",
        )

    # Mock provider (development / testing)
    return (
        MeetingProviderStatus.CONFIGURED,
        "Proveedor de reuniones interactivo (Mock habilitado).",
    )


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

