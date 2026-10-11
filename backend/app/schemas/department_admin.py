"""
PEVN Backend — Department Administrator Pydantic Schemas

Defines request and response validation contracts for the DEPARTMENT_ADMIN
lifecycle management API (creation, listing, profile editing, department
reassignment, and status transitions).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import DocumentType
from app.services.email_service import EmailDeliveryStatus


class DepartmentOptionResponse(BaseModel):
    """Canonical department selector option populated from the database."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    display_label: str


class DepartmentAdminCreateRequest(BaseModel):
    """Payload for creating a new DEPARTMENT_ADMIN user."""

    # Note: extra="ignore" allows incoming extra fields (e.g. client sending 'role': 'superadmin')
    # but the service strictly enforces SystemRole.DEPARTMENT_ADMIN server-side.
    model_config = ConfigDict(extra="ignore")

    first_name: str = Field(..., min_length=1, max_length=100, description="Nombres del administrador")
    last_name: str = Field(..., min_length=1, max_length=100, description="Apellidos del administrador")
    email: EmailStr = Field(..., description="Correo electrónico único del administrador")
    username: str = Field(..., min_length=3, max_length=100, description="Nombre de usuario handle único")
    department_id: uuid.UUID = Field(..., description="UUID canónico del departamento en la tabla departments")
    document_type: DocumentType = Field(default=DocumentType.CC, description="Tipo de documento de identidad")
    document_number: str | None = Field(default=None, description="Número de documento de identidad")
    password: str | None = Field(default=None, min_length=8, max_length=255, description="Contraseña inicial (opcional)")
    is_active: bool | None = Field(default=None, description="Estado operativo inicial")


class DepartmentAdminUpdateRequest(BaseModel):
    """Payload for modifying a DEPARTMENT_ADMIN profile."""

    model_config = ConfigDict(extra="forbid")

    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = None
    document_number: str | None = Field(None, min_length=3, max_length=50)
    is_active: bool | None = None


class DepartmentAdminReassignDepartmentRequest(BaseModel):
    """Payload for explicitly reassigning a DEPARTMENT_ADMIN to another department."""

    model_config = ConfigDict(extra="forbid")

    new_department_id: uuid.UUID = Field(..., description="UUID canónico del nuevo departamento")
    reason: str | None = Field(None, max_length=500, description="Motivo administrativo del traslado")


class DepartmentAdminStatusUpdateRequest(BaseModel):
    """Payload for activating or deactivating a DEPARTMENT_ADMIN."""

    model_config = ConfigDict(extra="forbid")

    is_active: bool = Field(..., description="True para activar, False para desactivar")
    reason: str | None = Field(None, max_length=500, description="Motivo administrativo del cambio de estado")


class DepartmentAdminResponse(BaseModel):
    """Authoritative API response schema for a DEPARTMENT_ADMIN user."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    full_name: str
    document_type: DocumentType
    document_number: str
    role: str = "department_admin"
    role_code: str = "department_admin"
    department_id: uuid.UUID
    department_code: str
    department_name: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime | None = None
    last_login_at: datetime | None = None
    raw_invitation_token: str | None = Field(
        None,
        description="Token de invitación de un solo uso (retornado únicamente tras emisión/reemisión)",
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


class DepartmentAdminInvitationResponse(BaseModel):
    """Response returned upon issuing or resending a department admin invitation."""

    model_config = ConfigDict(from_attributes=True)

    invitation_id: uuid.UUID
    department_id: uuid.UUID
    department_code: str
    department_name: str
    user_id: uuid.UUID
    email: EmailStr
    expires_at: datetime
    is_used: bool
    raw_invitation_token: str | None = Field(
        None,
        description="One-time raw token returned to the administrator for dispatching.",
    )
    email_delivery_status: EmailDeliveryStatus = Field(
        default=EmailDeliveryStatus.EMAIL_NOT_CONFIGURED,
        description="Estado de despacho del correo institucional",
    )
    invitation_url: str | None = Field(
        default=None,
        description="Enlace directo de activación para fallback cuando el correo no está disponible",
    )


class DepartmentAdminKPIs(BaseModel):
    """Authoritative server-side KPI counts for department administrators."""

    total: int = Field(..., description="Total de administradores departamentales registrados con territorio asignado")
    active: int = Field(..., description="Administradores con estado activo habilitado")
    inactive: int = Field(..., description="Administradores inactivos o suspendidos")
    departments_covered: int = Field(..., description="Cantidad de departamentos distintos con al menos un administrador")
    total_canonical_departments: int = Field(default=33, description="Total de entidades territoriales canónicas nacionales (33)")


class DepartmentAdminListResponse(BaseModel):
    """Paginated response for DEPARTMENT_ADMIN listing."""

    items: list[DepartmentAdminResponse]
    total: int
    page: int
    page_size: int
    kpis: DepartmentAdminKPIs | None = None
