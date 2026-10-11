"""
PEVN Backend — Institution & Campus Pydantic Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CampusResponse(BaseModel):
    """Campus response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    dane_sede_code: str
    name: str
    address: str | None = None
    is_active: bool


class InstitutionCreate(BaseModel):
    """Payload for creating a new institution."""

    model_config = ConfigDict(extra="forbid")

    municipality_id: uuid.UUID | str = Field(
        ...,
        description="ID interno (UUID) o Código DANE de 5 dígitos del municipio",
    )
    dane_code: str = Field(..., min_length=12, max_length=12, description="Código DANE oficial de 12 dígitos")
    name: str = Field(..., min_length=3, max_length=255)
    email: EmailStr
    phone: str | None = Field(None, max_length=50)
    address: str | None = Field(None, max_length=255)
    main_campus_name: str = Field("Sede Principal", max_length=255)
    main_campus_dane: str | None = Field(None, max_length=20)


class InstitutionStatusUpdateRequest(BaseModel):
    """Payload for updating institution operational status."""

    model_config = ConfigDict(extra="forbid")

    is_active: bool


class InstitutionUpdate(BaseModel):
    """Payload for updating institution details."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(None, min_length=3, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=50)
    address: str | None = Field(None, max_length=255)
    is_active: bool | None = None


class InstitutionResponse(BaseModel):
    """Institution response schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    municipality_id: uuid.UUID
    dane_code: str
    name: str
    email: EmailStr
    phone: str | None = None
    address: str | None = None
    is_active: bool
    coordinator_delegation_enabled: bool = False
    campuses: list[CampusResponse] = Field(default_factory=list)
    has_active_rector: bool = False
    active_rector_name: str | None = None
    active_rector_email: str | None = None
    has_pending_invitation: bool = False
    created_at: datetime
    updated_at: datetime


class InstitutionListResponse(BaseModel):
    """Paginated list of institutions."""

    items: list[InstitutionResponse]
    total: int
    page: int
    page_size: int


class CoordinatorDelegationSettingUpdateRequest(BaseModel):
    """Payload for updating Coordinator delegation setting (Rector-controlled)."""

    model_config = ConfigDict(extra="forbid")

    coordinator_delegation_enabled: bool = Field(
        ...,
        description="Whether Coordinators in this institution may create/manage Teachers, Students, and Guardians.",
    )


class CoordinatorDelegationSettingResponse(BaseModel):
    """Response schema for Coordinator delegation setting."""

    institution_id: uuid.UUID
    coordinator_delegation_enabled: bool
    updated_at: datetime


class OfficialCatalogItemResponse(BaseModel):
    """Authoritative catalog establishment with real-time PEVN lifecycle status."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dane_code: str
    name: str
    department_code: str
    department_name: str
    municipality_code: str
    municipality_name: str
    official_address: str | None = None
    official_phone: str | None = None
    official_email: str | None = None
    sector: str = "OFICIAL"
    zone: str = "URBANA"
    campus_count: int = 1
    is_active: bool = True
    is_provisioned: bool = False
    institution_id: uuid.UUID | None = None
    lifecycle_status: str  # DISPONIBLE_PARA_APROVISIONAR | APROVISIONADA_SIN_RECTOR | INVITACION_RECTOR_PENDIENTE | RECTOR_ACTIVO | INACTIVA
    has_active_rector: bool = False
    active_rector_name: str | None = None
    active_rector_email: str | None = None
    has_pending_invitation: bool = False


class OfficialCatalogSummary(BaseModel):
    """Summary counts for official catalog explorer within territorial scope."""

    total_catalog: int = 0
    available: int = 0
    provisioned: int = 0
    sin_rector: int = 0
    pending_invite: int = 0
    active_rector: int = 0
    inactiva: int = 0


class OfficialCatalogListResponse(BaseModel):
    """Paginated list of official catalog establishments with territorial scoping."""

    items: list[OfficialCatalogItemResponse]
    total: int
    page: int
    page_size: int
    summary: OfficialCatalogSummary


class ProvisionCatalogInstitutionRequest(BaseModel):
    """Payload for provisioning an official establishment as a PEVN tenant."""

    model_config = ConfigDict(extra="forbid")

    dane_code: str = Field(..., min_length=12, max_length=12, description="Código DANE oficial de 12 dígitos")
    contact_email: EmailStr | None = Field(None, description="Correo electrónico institucional de contacto")
    contact_phone: str | None = Field(None, max_length=50, description="Teléfono de contacto")
