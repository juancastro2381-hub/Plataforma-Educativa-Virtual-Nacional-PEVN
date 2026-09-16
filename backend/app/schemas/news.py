"""
PEVN Backend — Institutional News Schemas (Phase 15)

Pydantic schemas for community news, achievements, cultural/sports highlights.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.models.communication import PublishingStatus
from app.models.news import NewsCategory
from app.schemas.user import UserResponse


class NewsCreateRequest(BaseModel):
    """Payload for creating a new institutional news item."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=3, max_length=200, description="Headline")
    summary: str = Field(..., min_length=3, max_length=500, description="Lead/Summary")
    content: str = Field(..., min_length=5, description="Full story content")
    category: NewsCategory = Field(default=NewsCategory.NOTICIA_GENERAL, description="Category")
    cover_image_url: str | None = Field(default=None, max_length=500, description="Cover image URL")
    status: PublishingStatus = Field(default=PublishingStatus.PUBLICADO, description="Publishing state")


class NewsUpdateRequest(BaseModel):
    """Payload for modifying an existing news item."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=3, max_length=200)
    summary: str | None = Field(default=None, min_length=3, max_length=500)
    content: str | None = Field(default=None, min_length=5)
    category: NewsCategory | None = None
    cover_image_url: str | None = None
    status: PublishingStatus | None = None


class InstitutionalNewsResponse(BaseModel):
    """Response representation of an institutional news item."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    author_user_id: uuid.UUID
    title: str
    summary: str
    content: str
    category: NewsCategory
    cover_image_url: str | None = None
    status: PublishingStatus
    published_at: datetime | None = None
    author: UserResponse | None = None
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def author_name(self) -> str:
        if self.author:
            return f"{self.author.first_name} {self.author.last_name}".strip()
        return "Institución Educativa"

    @computed_field
    @property
    def is_published(self) -> bool:
        return self.status == PublishingStatus.PUBLICADO


class NewsListResponse(BaseModel):
    """List response for institutional news items."""

    items: list[InstitutionalNewsResponse]
    total: int
