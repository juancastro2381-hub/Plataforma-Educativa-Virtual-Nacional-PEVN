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


class RectorRevocationRequest(BaseModel):
    """Payload for revoking the active Rector of an educational institution."""

    model_config = ConfigDict(extra="forbid")

    reason: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Motivo oficial de la revocación o declaratoria de vacancia",
    )
    justification: str | None = Field(
        None,
        max_length=500,
        description="Acto administrativo, resolución ministerial o justificación detallada",
    )


class RectorRevocationResponse(BaseModel):
    """Response returned upon successfully revoking a Rector."""

    institution_id: uuid.UUID
    revoked_user_id: uuid.UUID
    revoked_rector_email: str
    revoked_rector_name: str
    reason: str
    revoked_at: datetime
    message: str


class GuardianActivationRequest(BaseModel):
    """Payload for requesting activation of an enrolled student's guardian account."""

    model_config = ConfigDict(extra="forbid")

    student_code_simat: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Código SIMAT o número de matrícula oficial del estudiante",
    )
    guardian_document_type: DocumentType = Field(
        ...,
        description="Tipo de documento de identidad del acudiente",
    )
    guardian_document_number: str = Field(
        ...,
        min_length=4,
        max_length=50,
        description="Número de documento de identidad civil del acudiente",
    )
    email: EmailStr = Field(
        ...,
        description="Correo electrónico donde se remitirá el enlace de activación",
    )


class GuardianActivationResponse(BaseModel):
    """Response returned upon requesting guardian activation."""

    message: str
    raw_activation_token: str | None = Field(
        None,
        description="Token de activación de un solo uso retornado para entrega directa / despacho.",
    )


class VerifyGuardianTokenRequest(BaseModel):
    """Payload for validating a guardian onboarding token."""

    model_config = ConfigDict(extra="forbid")

    token: str = Field(..., min_length=10)


class VerifyGuardianTokenResponse(BaseModel):
    """Response returned upon validating a guardian onboarding token."""

    valid: bool
    guardian_name: str
    student_name: str
    institution_name: str
    email: str
    expires_at: datetime


class GuardianAcceptActivationRequest(BaseModel):
    """Payload for redeeming a guardian onboarding token and setting credentials."""

    model_config = ConfigDict(extra="forbid")

    token: str = Field(..., min_length=10)
    password: str = Field(..., min_length=8, max_length=128)
    password_confirmation: str = Field(..., min_length=8, max_length=128)


class GuardianAcceptActivationResponse(BaseModel):
    """Response returned upon successful guardian onboarding completion."""

    message: str
    user_id: uuid.UUID
    email: EmailStr
    is_active: bool
