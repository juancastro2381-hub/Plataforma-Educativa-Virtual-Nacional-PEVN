"""
PEVN Backend — Rector Invitation & Onboarding Pydantic Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import DocumentType


class RectorInvitationCreateRequest(BaseModel):
    """Payload for issuing a new rector onboarding invitation."""

    model_config = ConfigDict(extra="forbid")

    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    document_type: DocumentType
    document_number: str = Field(..., min_length=4, max_length=50)
    email: EmailStr
    phone_number: str | None = Field(None, max_length=50)


class RectorInvitationResponse(BaseModel):
    """Response returned upon issuing a rector invitation."""

    model_config = ConfigDict(from_attributes=True)

    invitation_id: uuid.UUID
    institution_id: uuid.UUID
    user_id: uuid.UUID
    email: EmailStr
    expires_at: datetime
    is_used: bool
    raw_invitation_token: str | None = Field(
        None,
        description="One-time raw token returned to the administrator for dispatching.",
    )


class VerifyInvitationRequest(BaseModel):
    """Payload for validating an invitation token."""

    model_config = ConfigDict(extra="forbid")

    token: str = Field(..., min_length=10)


class VerifyInvitationResponse(BaseModel):
    """Response returned upon validating an invitation token."""

    valid: bool
    email: str
    first_name: str
    last_name: str
    institution_name: str
    expires_at: datetime


class AcceptInvitationRequest(BaseModel):
    """Payload for redeeming an invitation and defining credentials."""

    model_config = ConfigDict(extra="forbid")

    token: str = Field(..., min_length=10)
    password: str = Field(..., min_length=8, max_length=128)
    password_confirmation: str = Field(..., min_length=8, max_length=128)


class AcceptInvitationResponse(BaseModel):
    """Response returned upon successful onboarding completion."""

    message: str
    user_id: uuid.UUID
    email: EmailStr
    is_active: bool
