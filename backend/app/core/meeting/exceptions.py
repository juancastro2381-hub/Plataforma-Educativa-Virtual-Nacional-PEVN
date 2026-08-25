"""
PEVN Backend — Meeting Provider Exceptions

Domain-neutral error hierarchy for virtual classroom and meeting provider operations.
"""

from __future__ import annotations

from http import HTTPStatus

from app.exceptions.errors import PEVNException


class MeetingProviderError(PEVNException):
    """Base exception for meeting provider failures."""

    default_code = "MEETING_PROVIDER_ERROR"
    default_status = HTTPStatus.BAD_GATEWAY

    def __init__(
        self,
        message: str = "Error en el proveedor de aulas virtuales.",
        code: str | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code or self.default_code,
            status_code=status_code or self.default_status,
        )


class MeetingProviderConfigError(MeetingProviderError):
    """Raised when meeting provider is misconfigured or missing credentials."""

    default_code = "MEETING_PROVIDER_CONFIG_ERROR"
    default_status = HTTPStatus.INTERNAL_SERVER_ERROR

    def __init__(
        self,
        message: str = "Configuración inválida o incompleta del proveedor.",
    ) -> None:
        super().__init__(
            message=message,
            code=self.default_code,
            status_code=self.default_status,
        )


class MeetingProviderAuthError(MeetingProviderError):
    """Raised when provider signature or credential authentication fails."""

    default_code = "MEETING_PROVIDER_AUTH_ERROR"
    default_status = HTTPStatus.BAD_GATEWAY

    def __init__(
        self,
        message: str = "Fallo de autenticación o firma con el servidor.",
    ) -> None:
        super().__init__(
            message=message,
            code=self.default_code,
            status_code=self.default_status,
        )


class MeetingProviderConnectionError(MeetingProviderError):
    """Raised when communication with the provider server times out or fails."""

    default_code = "MEETING_PROVIDER_CONNECTION_ERROR"
    default_status = HTTPStatus.SERVICE_UNAVAILABLE

    def __init__(
        self,
        message: str = "No fue posible conectar con el servidor de videoconferencias.",
    ) -> None:
        super().__init__(
            message=message,
            code=self.default_code,
            status_code=self.default_status,
        )


class MeetingNotFoundError(MeetingProviderError):
    """Raised when target meeting session does not exist on the provider server."""

    default_code = "MEETING_NOT_FOUND"
    default_status = HTTPStatus.NOT_FOUND

    def __init__(
        self,
        message: str = "La reunión solicitada no existe o ha expirado en el servidor.",
    ) -> None:
        super().__init__(
            message=message,
            code=self.default_code,
            status_code=self.default_status,
        )


class MeetingProviderResponseError(MeetingProviderError):
    """Raised when provider returns an unparseable or error response."""

    default_code = "MEETING_PROVIDER_RESPONSE_ERROR"
    default_status = HTTPStatus.BAD_GATEWAY

    def __init__(
        self,
        message: str = "Respuesta inválida devuelta por el servidor.",
    ) -> None:
        super().__init__(
            message=message,
            code=self.default_code,
            status_code=self.default_status,
        )
