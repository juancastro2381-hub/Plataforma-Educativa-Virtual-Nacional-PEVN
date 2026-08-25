"""
PEVN Backend — Authentication & Authorization Pydantic Schemas

Strict validation schemas for login, token refresh, password recovery,
and authorization context serialization.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import DocumentType


class LoginRequest(BaseModel):
    """Credentials payload for authentication."""

    model_config = ConfigDict(extra="forbid")

    username: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Username handle or email address",
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Plaintext password (scrubbed from all logs and responses)",
    )


class RoleResponse(BaseModel):
    """Role information."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    display_name: str
    level: int


class PermissionResponse(BaseModel):
    """Permission information."""

    model_config = ConfigDict(from_attributes=True)

    resource: str
    action: str
    identifier: str


class ScopeResponse(BaseModel):
    """Organizational scope boundaries."""

    country_code: str | None = "CO"
    department_id: str | None = None
    municipality_id: str | None = None
    institution_id: str | None = None
    campus_id: str | None = None
    is_national: bool
    is_institution: bool


class UserMeResponse(BaseModel):
    """Authenticated user profile and authorization context."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    full_name: str
    document_type: DocumentType
    document_number: str
    institution_id: uuid.UUID | None = None
    is_active: bool
    is_verified: bool
    must_change_password: bool
    roles: list[str]
    permissions: list[str]
    scope: ScopeResponse


class LoginResponse(BaseModel):
    """Successful authentication response payload."""

    access_token: str
    token_type: str = "bearer"  # noqa: S105
    expires_in: int = 900  # 15 minutes in seconds
    user: UserMeResponse


class TokenRefreshResponse(BaseModel):
    """Token rotation response payload."""

    access_token: str
    token_type: str = "bearer"  # noqa: S105
    expires_in: int = 900


class PasswordChangeRequest(BaseModel):
    """Password update payload."""

    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(..., min_length=1, max_length=255)
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=255,
        description="New password meeting complexity rules",
    )


class PasswordResetRequest(BaseModel):
    """Password reset initiation payload."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(..., description="Registered email address")


class PasswordResetConfirmRequest(BaseModel):
    """Password reset execution payload."""

    model_config = ConfigDict(extra="forbid")

    token: str = Field(..., min_length=10, description="Single-use reset token")
    new_password: str = Field(..., min_length=8, max_length=255)
