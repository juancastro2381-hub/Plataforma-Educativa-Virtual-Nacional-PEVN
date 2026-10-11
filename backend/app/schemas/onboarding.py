"""
PEVN Backend — Institution Onboarding Workflow Pydantic Schemas

Defines request payloads and serialized response representations for the
NTA-04 National Provisioning Workflow.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CatalogExplorerItemResponse(BaseModel):
    """
    Catalog establishment enriched with PEVN onboarding and tenant state.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dane_code: str
    name: str
    department_code: str
    department_name: str
    department_id: uuid.UUID | None = None
    municipality_code: str
    municipality_name: str
    municipality_id: uuid.UUID | None = None
    official_address: str | None = None
    sector: str | None = None
    is_active: bool
    principal_campus_name: str | None = None
    campus_count: int = 1
    onboarding_status: str  # 'AVAILABLE' | 'EN_TRAMITE' | 'PROVISIONED'
    active_request_id: uuid.UUID | None = None
    active_request_number: str | None = None
    institution_id: uuid.UUID | None = None


class CatalogExplorerListResponse(BaseModel):
    """Paginated response for catalog exploration."""

    items: list[CatalogExplorerItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class OnboardingRequestCreatePayload(BaseModel):
    """Payload to create or submit an onboarding request."""

    model_config = ConfigDict(extra="forbid")

    catalog_institution_id: uuid.UUID = Field(
        ...,
        description="ID del establecimiento en official_institution_catalog",
    )
    contact_email: EmailStr = Field(
        ...,
        description="Correo institucional oficial para la institución en PEVN",
    )
    contact_phone: str | None = Field(
        None,
        max_length=50,
        description="Teléfono institucional de contacto",
    )
    proposed_rector_name: str | None = Field(
        None,
        max_length=255,
        description="Nombre completo del Rector designado",
    )
    proposed_rector_email: EmailStr | None = Field(
        None,
        description="Correo electrónico oficial del Rector",
    )
    proposed_rector_doc_type: str | None = Field(
        None,
        max_length=20,
        description="Tipo de documento (CC, CE)",
    )
    proposed_rector_doc_num: str | None = Field(
        None,
        max_length=50,
        description="Número de documento de identidad del Rector",
    )
    justification: str | None = Field(
        None,
        description="Justificación administrativa de la incorporación",
    )
    is_draft: bool = Field(
        False,
        description="True para guardar en borrador DRAFT, False para radicar SUBMITTED",
    )
    idempotency_key: str | None = Field(
        None,
        max_length=64,
        description="Clave de idempotencia única del cliente",
    )


class OnboardingApprovalPayload(BaseModel):
    """Payload for approving an onboarding request."""

    model_config = ConfigDict(extra="forbid")

    notes: str | None = Field(
        None,
        description="Observaciones o notas administrativas de aprobación",
    )


class OnboardingRejectionPayload(BaseModel):
    """Payload for rejecting an onboarding request."""

    model_config = ConfigDict(extra="forbid")

    rejection_reason: str = Field(
        ...,
        min_length=10,
        description="Motivo formal y obligatorio de rechazo (mínimo 10 caracteres)",
    )


class OnboardingCancellationPayload(BaseModel):
    """Payload for cancelling an onboarding request."""

    model_config = ConfigDict(extra="forbid")

    cancellation_reason: str | None = Field(
        None,
        description="Motivo voluntario del desistimiento de la solicitud",
    )


class OnboardingRequestDetailResponse(BaseModel):
    """Comprehensive representation of an onboarding request."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    request_number: str
    catalog_institution_id: uuid.UUID
    dane_code: str
    institution_name: str | None = None
    department_id: uuid.UUID
    department_name: str | None = None
    department_code: str | None = None
    municipality_id: uuid.UUID
    municipality_name: str | None = None
    municipality_code: str | None = None
    requested_by_id: uuid.UUID
    requester_name: str | None = None
    requester_email: str | None = None
    requester_role: str
    status: str
    institution_id: uuid.UUID | None = None
    contact_email: str
    contact_phone: str | None = None
    proposed_rector_name: str | None = None
    proposed_rector_email: str | None = None
    proposed_rector_doc_type: str | None = None
    proposed_rector_doc_num: str | None = None
    justification: str | None = None
    reviewed_by_id: uuid.UUID | None = None
    reviewed_by_name: str | None = None
    reviewed_at: datetime | None = None
    review_notes: str | None = None
    approved_by_id: uuid.UUID | None = None
    approved_by_name: str | None = None
    approved_at: datetime | None = None
    rejected_by_id: uuid.UUID | None = None
    rejected_by_name: str | None = None
    rejected_at: datetime | None = None
    rejection_reason: str | None = None
    cancelled_by_id: uuid.UUID | None = None
    cancelled_by_name: str | None = None
    cancelled_at: datetime | None = None
    cancellation_reason: str | None = None
    provisioned_by_id: uuid.UUID | None = None
    provisioned_by_name: str | None = None
    provisioned_at: datetime | None = None
    lock_version: int = 0
    idempotency_key: str | None = None
    created_at: datetime
    updated_at: datetime


class OnboardingRequestListResponse(BaseModel):
    """Paginated response for onboarding request management queue."""

    items: list[OnboardingRequestDetailResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class OnboardingProvisionResultResponse(BaseModel):
    """Result of executing atomic institution provisioning from onboarding."""

    model_config = ConfigDict(from_attributes=True)

    request_id: uuid.UUID
    request_number: str
    institution_id: uuid.UUID
    institution_name: str
    dane_code: str
    campuses_created: int
    rector_invited: bool
    rector_status: str  # 'INVITED' | 'PENDING_ASSIGNMENT'
    rector_invitation_id: uuid.UUID | None = None
    activation_url: str | None = None
    raw_invitation_token: str | None = None
