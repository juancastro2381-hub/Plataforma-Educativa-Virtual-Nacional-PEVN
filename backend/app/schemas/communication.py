"""
PEVN Backend — Institutional Communications Schemas (Phase 15)

Pydantic schemas for communications, audience targeting, and read-receipt tracking.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.communication import (
    CommunicationCategory,
    CommunicationPriority,
    PublishingStatus,
    TargetScopeType,
)
from app.schemas.user import UserResponse


class CommunicationAudiencePayload(BaseModel):
    """Audience targeting payload."""

    model_config = ConfigDict(extra="forbid")

    campus_id: uuid.UUID | None = Field(default=None, description="Target campus / sede")
    grade_id: uuid.UUID | None = Field(default=None, description="Target grade")
    group_id: uuid.UUID | None = Field(default=None, description="Target group section")
    role_name: str | None = Field(default=None, description="Target role ('student', 'guardian', 'teacher')")


class CommunicationCreateRequest(BaseModel):
    """Payload for creating a new institutional communication."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=3, max_length=200, description="Title/Subject")
    summary: str = Field(..., min_length=3, max_length=500, description="Summary")
    content: str = Field(..., min_length=5, description="Full Markdown body")
    category: CommunicationCategory = Field(
        default=CommunicationCategory.CIRCULAR_OFICIAL,
        description="Official category",
    )
    priority: CommunicationPriority = Field(
        default=CommunicationPriority.MEDIA,
        description="Priority / Urgency",
    )
    target_scope: TargetScopeType = Field(
        default=TargetScopeType.TODOS_INSTITUCION,
        description="Scope boundary",
    )
    attachment_url: str | None = Field(default=None, max_length=500, description="PDF attachment URL")
    requires_acknowledgment: bool = Field(default=False, description="Require formal read receipt")
    status: PublishingStatus = Field(default=PublishingStatus.PUBLICADO, description="Publishing state")
    expires_at: datetime | None = Field(default=None, description="Expiration date for active feeds")
    audiences: list[CommunicationAudiencePayload] | None = Field(
        default=None,
        description="Granular audience targets if target_scope is specific",
    )


class CommunicationUpdateRequest(BaseModel):
    """Payload for modifying an existing communication."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=3, max_length=200)
    summary: str | None = Field(default=None, min_length=3, max_length=500)
    content: str | None = Field(default=None, min_length=5)
    category: CommunicationCategory | None = None
    priority: CommunicationPriority | None = None
    target_scope: TargetScopeType | None = None
    attachment_url: str | None = None
    requires_acknowledgment: bool | None = None
    status: PublishingStatus | None = None
    expires_at: datetime | None = None
    audiences: list[CommunicationAudiencePayload] | None = None


class CommunicationAudienceResponse(BaseModel):
    """Audience response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    communication_id: uuid.UUID
    campus_id: uuid.UUID | None = None
    grade_id: uuid.UUID | None = None
    group_id: uuid.UUID | None = None
    role_name: str | None = None


class CommunicationReceiptResponse(BaseModel):
    """Read receipt response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    communication_id: uuid.UUID
    user_id: uuid.UUID
    read_at: datetime
    acknowledged_at: datetime | None = None
    is_acknowledged: bool = False


class InstitutionalCommunicationResponse(BaseModel):
    """Response representation of an institutional communication."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    author_user_id: uuid.UUID
    title: str
    summary: str
    content: str
    category: CommunicationCategory
    priority: CommunicationPriority
    target_scope: TargetScopeType
    attachment_url: str | None = None
    requires_acknowledgment: bool = False
    status: PublishingStatus
    published_at: datetime | None = None
    expires_at: datetime | None = None
    is_expired: bool = False
    is_active: bool = True
    author: UserResponse | None = None
    audiences: list[CommunicationAudienceResponse] = []
    # Dynamic receipt fields for the caller context
    is_read: bool = False
    is_acknowledged: bool = False
    read_at: datetime | None = None
    acknowledged_at: datetime | None = None
    total_receipts_count: int = 0
    acknowledged_receipts_count: int = 0
    created_at: datetime
    updated_at: datetime


class CommunicationListResponse(BaseModel):
    """List response for institutional communications."""

    items: list[InstitutionalCommunicationResponse]
    total: int
    unread_count: int = 0


class AcknowledgeCommunicationRequest(BaseModel):
    """Payload for acknowledging an institutional communication."""

    model_config = ConfigDict(extra="forbid")
    client_ip: str | None = None
