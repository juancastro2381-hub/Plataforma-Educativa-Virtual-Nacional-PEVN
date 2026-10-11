"""
PEVN Backend — Municipality Admin Pydantic Schemas

Strict validation schemas for MUNICIPALITY_ADMIN lifecycle, provisioning,
territorial jurisdiction inspection, and options list.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import DocumentType
from app.services.email_service import EmailDeliveryStatus


class MunicipalityOptionResponse(BaseModel):
    """Canonical municipality option for territorial selection."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    department_id: uuid.UUID
    department_code: str | None = None
    department_name: str | None = None
    display_label: str


class MunicipalityAdminCreateRequest(BaseModel):
    """Request payload to provision a new Municipality Administrator."""

    model_config = ConfigDict(extra="forbid")

    municipality_id: uuid.UUID = Field(
        ...,
        description="UUID del municipio canónico asignado (la jurisdicción departamental se deriva de forma autoritativa)",
    )
    email: EmailStr = Field(..., description="Correo electrónico institucional único")
    username: str = Field(..., min_length=3, max_length=50, description="Identificador único de usuario")
    first_name: str = Field(..., min_length=1, max_length=100, description="Nombres del administrador")
    last_name: str = Field(..., min_length=1, max_length=100, description="Apellidos del administrador")
    document_type: DocumentType = Field(default=DocumentType.CC, description="Tipo de documento")
    document_number: str | None = Field(default=None, max_length=50, description="Número de documento de identidad")


class MunicipalityAdminResponse(BaseModel):
    """Authoritative response representation of a Municipality Administrator."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    username: str
    first_name: str
    last_name: str
    full_name: str
    document_type: DocumentType
    document_number: str
    is_active: bool
    is_verified: bool
    roles: list[str]
    municipality_id: uuid.UUID
    municipality_code: str
    municipality_name: str
    department_id: uuid.UUID
    department_code: str
    department_name: str
    created_at: datetime
    raw_invitation_token: str | None = Field(
        None,
        description="Token de invitación de un solo uso (retornado únicamente en desarrollo tras emisión)",
    )
    invitation_id: uuid.UUID | None = Field(
        None,
        description="UUID de la invitación generada",
    )
    email_delivery_status: EmailDeliveryStatus = Field(
        default=EmailDeliveryStatus.EMAIL_NOT_CONFIGURED,
        description="Estado de despacho del correo institucional",
    )
    invitation_url: str | None = Field(
        default=None,
        description="Enlace directo de activación para fallback cuando el correo no está disponible",
    )


class MunicipalityAdminInvitationResponse(BaseModel):
    """Response returned upon issuing or resending a municipality admin invitation."""

    model_config = ConfigDict(from_attributes=True)

    invitation_id: uuid.UUID
    municipality_id: uuid.UUID
    municipality_code: str
    municipality_name: str
    user_id: uuid.UUID
    email: EmailStr
    expires_at: datetime
    is_used: bool
    raw_invitation_token: str | None = Field(
        None,
        description="One-time raw token returned to the administrator for manual delivery in development.",
    )
    email_delivery_status: EmailDeliveryStatus = Field(
        default=EmailDeliveryStatus.EMAIL_NOT_CONFIGURED,
        description="Estado de despacho del correo institucional",
    )
    invitation_url: str | None = Field(
        default=None,
        description="Enlace directo de activación para fallback cuando el correo no está disponible",
    )


class MunicipalityAdminListResponse(BaseModel):
    """Paginated list of Municipality Administrators."""

    model_config = ConfigDict(from_attributes=True)

    items: list[MunicipalityAdminResponse]
    total: int
    page: int
    page_size: int


class MunicipalityAdminUpdateRequest(BaseModel):
    """Payload to update Municipality Administrator profile details."""

    model_config = ConfigDict(extra="forbid")

    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None


class MunicipalityAdminStatusUpdateRequest(BaseModel):
    """Payload to activate or deactivate a Municipality Administrator."""

    model_config = ConfigDict(extra="forbid")

    is_active: bool
    reason: str | None = Field(default=None, max_length=500)


class MunicipalityAdminReassignMunicipalityRequest(BaseModel):
    """Payload to reassign a Municipality Administrator to another municipality."""

    model_config = ConfigDict(extra="forbid")

    new_municipality_id: uuid.UUID
    reason: str | None = Field(default=None, max_length=500)

