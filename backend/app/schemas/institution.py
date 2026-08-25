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

    municipality_id: uuid.UUID
    dane_code: str = Field(..., min_length=5, max_length=20)
    name: str = Field(..., min_length=3, max_length=255)
    email: EmailStr
    phone: str | None = Field(None, max_length=50)
    address: str | None = Field(None, max_length=255)


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
    campuses: list[CampusResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
