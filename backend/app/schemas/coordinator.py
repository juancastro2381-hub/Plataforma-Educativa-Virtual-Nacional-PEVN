"""
PEVN Backend — Coordinator Pydantic Schemas

Strict validation schemas for institutional COORDINATOR lifecycle, provisioning,
and management.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import DocumentType
from app.services.email_service import EmailDeliveryStatus


class CoordinatorCampusOption(BaseModel):
    """Available campus option for institutional assignment."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    dane_sede_code: str
    name: str
    is_main: bool = False
    is_active: bool = True


class CoordinatorCreateRequest(BaseModel):
    """Payload to provision a new Coordinator in the institutional context."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(..., description="Correo electrónico único del coordinador")
    first_name: str = Field(..., min_length=1, max_length=100, description="Nombres del coordinador")
    last_name: str = Field(..., min_length=1, max_length=100, description="Apellidos del coordinador")
    document_type: DocumentType = Field(default=DocumentType.CC, description="Tipo de documento")
    document_number: str = Field(..., min_length=3, max_length=50, description="Número de documento")
    campus_id: uuid.UUID | None = Field(default=None, description="ID opcional de la sede educativa asignada")
    password: str | None = Field(default=None, min_length=8, description="Contraseña inicial opcional (para aprovisionamiento directo)")
    is_active: bool = Field(default=False, description="Estado de activación inicial (False para flujo de invitación)")


class CoordinatorResponse(BaseModel):
    """Authoritative response representation of an Institutional Coordinator."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    campus_id: uuid.UUID | None = None
    campus_name: str | None = None
    email: str
    username: str
    first_name: str
    last_name: str
    full_name: str
    document_type: DocumentType
    document_number: str
    role: str = "coordinator"
    is_active: bool
    is_verified: bool
    created_at: datetime

    # Invitation metadata
    invitation_id: uuid.UUID | None = None
    invitation_status: str | None = None  # "pending", "accepted", "expired", "revoked", "direct"
    raw_invitation_token: str | None = None
    invitation_url: str | None = None
    email_delivery_status: EmailDeliveryStatus | None = None


class CoordinatorListResponse(BaseModel):
    """Paginated response of institutional coordinators."""

    model_config = ConfigDict(from_attributes=True)

    items: list[CoordinatorResponse]
    total: int
    page: int
    page_size: int


class CoordinatorStatusUpdateRequest(BaseModel):
    """Payload to update active status of a Coordinator."""

    model_config = ConfigDict(extra="forbid")

    is_active: bool
    reason: str | None = Field(default=None, max_length=500)


class CoordinatorResendInvitationResponse(BaseModel):
    """Response returned when resending a coordinator invitation."""

    model_config = ConfigDict(from_attributes=True)

    invitation_id: uuid.UUID
    raw_invitation_token: str | None = None
    invitation_url: str | None = None
    email_delivery_status: EmailDeliveryStatus = EmailDeliveryStatus.EMAIL_NOT_CONFIGURED
    expires_at: datetime
    message: str
