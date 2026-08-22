"""
PEVN Backend — Application Exception Hierarchy

All domain exceptions inherit from PEVNException.
Exception handlers in app.exceptions.handlers catch these and
convert them into standardized API error responses.

Hierarchy:
    PEVNException
    ├── AuthenticationError (401)
    │   ├── InvalidCredentialsError
    │   ├── TokenExpiredError
    │   ├── TokenInvalidError
    │   └── AccountLockedError
    ├── AuthorizationError (403)
    │   ├── PermissionDeniedError
    │   └── InstitutionAccessDeniedError
    ├── NotFoundError (404)
    ├── ConflictError (409)
    ├── ValidationError (422)
    └── RateLimitExceededError (429)
"""

from __future__ import annotations

from http import HTTPStatus


class PEVNException(Exception):  # noqa: N818
    """
    Base class for all application exceptions.
    Ensures every error has an error code, message, and HTTP status.
    """

    default_code: str = "INTERNAL_ERROR"
    default_status: int = HTTPStatus.INTERNAL_SERVER_ERROR

    def __init__(
        self,
        message: str,
        code: str | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.default_code
        self.status_code = status_code or self.default_status

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(code={self.code!r}, message={self.message!r})"
        )


# ---- 4xx Client Errors ---------------------------------------------------


class NotFoundError(PEVNException):
    """404 Not Found — the requested resource does not exist."""

    def __init__(
        self,
        message: str = "Resource not found",
        code: str | None = None,
    ) -> None:
        super().__init__(message, code=code, status_code=HTTPStatus.NOT_FOUND)


class ConflictError(PEVNException):
    """409 Conflict — the request conflicts with current state."""

    def __init__(
        self,
        message: str = "Resource conflict",
        code: str | None = None,
    ) -> None:
        super().__init__(message, code=code, status_code=HTTPStatus.CONFLICT)


class UnprocessableEntityError(PEVNException):
    """422 Unprocessable Entity — valid request structure but invalid content."""

    def __init__(
        self,
        message: str = "Unprocessable entity",
        code: str | None = None,
    ) -> None:
        super().__init__(
            message,
            code=code,
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        )


# ---- Authentication Errors (401) -----------------------------------------


class AuthenticationError(PEVNException):
    """401 Unauthorized — authentication required or failed."""

    default_code = "AUTHENTICATION_FAILED"
    default_status = HTTPStatus.UNAUTHORIZED


class InvalidCredentialsError(AuthenticationError):
    """Invalid username or password provided."""

    default_code = "INVALID_CREDENTIALS"

    def __init__(
        self,
        message: str = "Invalid username or password",
    ) -> None:
        super().__init__(message, code=self.default_code)


class TokenExpiredError(AuthenticationError):
    """The provided token has expired."""

    default_code = "TOKEN_EXPIRED"

    def __init__(
        self,
        message: str = "Authentication token has expired",
    ) -> None:
        super().__init__(message, code=self.default_code)


class TokenInvalidError(AuthenticationError):
    """The provided token is malformed, invalid, or revoked."""

    default_code = "TOKEN_INVALID"

    def __init__(
        self,
        message: str = "Authentication token is invalid",
    ) -> None:
        super().__init__(message, code=self.default_code)


class AccountLockedError(AuthenticationError):
    """The account is locked due to too many failed login attempts."""

    default_code = "ACCOUNT_LOCKED"

    def __init__(
        self,
        message: str = "Account is temporarily locked. Please try again later.",
    ) -> None:
        super().__init__(message, code=self.default_code)


# ---- Authorization Errors (403) ------------------------------------------


class AuthorizationError(PEVNException):
    """403 Forbidden — user is authenticated but lacks required permission."""

    default_code = "PERMISSION_DENIED"
    default_status = HTTPStatus.FORBIDDEN


class PermissionDeniedError(AuthorizationError):
    """User lacks the specific permission required for this action."""

    default_code = "PERMISSION_DENIED"

    def __init__(
        self,
        permission: str,
        message: str | None = None,
    ) -> None:
        msg = message or f"Permission denied: required '{permission}'"
        super().__init__(msg, code=self.default_code)


class InstitutionAccessDeniedError(AuthorizationError):
    """User's scope does not permit access to the target institution's data."""

    default_code = "INSTITUTION_ACCESS_DENIED"

    def __init__(
        self,
        institution_id: str,
        message: str | None = None,
    ) -> None:
        msg = message or f"Access to institution '{institution_id}' is not permitted"
        super().__init__(msg, code=self.default_code)


# ---- Rate Limiting (429) --------------------------------------------------


class RateLimitExceededError(PEVNException):
    """429 Too Many Requests — client has exceeded the rate limit."""

    def __init__(
        self,
        message: str = "Too many requests. Please try again later.",
    ) -> None:
        super().__init__(
            message,
            code="RATE_LIMIT_EXCEEDED",
            status_code=HTTPStatus.TOO_MANY_REQUESTS,
        )
