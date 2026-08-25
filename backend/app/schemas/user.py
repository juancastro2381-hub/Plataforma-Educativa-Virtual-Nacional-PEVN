"""
PEVN Backend — User Management Pydantic Schemas
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import DocumentType


class UserCreate(BaseModel):
    """Payload for creating a new user account."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8, max_length=255)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    document_type: DocumentType = DocumentType.CC
    document_number: str = Field(..., min_length=3, max_length=50)
    institution_id: uuid.UUID | None = None
    role_names: list[str] = Field(default_factory=lambda: ["student"])


class UserUpdate(BaseModel):
    """Payload for updating user profile fields."""

    model_config = ConfigDict(extra="forbid")

    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    is_active: bool | None = None
    must_change_password: bool | None = None


class UserResponse(BaseModel):
    """Public user response schema."""

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
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    """Paginated user listing response."""

    items: list[UserResponse]
    total: int
    page: int
    page_size: int
