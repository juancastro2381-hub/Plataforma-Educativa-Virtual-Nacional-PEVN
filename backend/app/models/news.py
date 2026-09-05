"""
PEVN Backend — Institutional News Domain Model (Phase 15 - DECISION-15-03)

Community highlights, academic achievements, cultural/sports activities, and general news.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.communication import PublishingStatus

if TYPE_CHECKING:
    from app.models.institution import Institution
    from app.models.user import User


class NewsCategory(enum.StrEnum):
    """
    Categorization for institutional community news.
    """

    LOGRO_ACADEMICO = "LOGRO_ACADEMICO"
    EVENTO_CULTURAL = "EVENTO_CULTURAL"
    EVENTO_DEPORTIVO = "EVENTO_DEPORTIVO"
    PROYECTO_INSTITUCIONAL = "PROYECTO_INSTITUCIONAL"
    NOTICIA_GENERAL = "NOTICIA_GENERAL"


class InstitutionalNews(Base):
    """
    Institutional News Entity (Noticia Escolar / Revista Institucional).

    Represents community-oriented updates, celebrations, student achievements,
    and cultural events. Distinct from formal binding communications per DECISION-15-03.
    """

    __tablename__ = "institutional_news"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Authoring educational institution tenant boundary.",
    )
    author_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="User who drafted or published the news item.",
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Headline/title of the news item.",
    )
    summary: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Lead paragraph or short excerpt.",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Full news body text (supports rich formatting/Markdown).",
    )
    category: Mapped[NewsCategory] = mapped_column(
        SQLEnum(
            NewsCategory,
            name="news_category_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=NewsCategory.NOTICIA_GENERAL,
        doc="Thematic news category.",
    )
    cover_image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Optional URL/path to a high-resolution cover image.",
    )
    status: Mapped[PublishingStatus] = mapped_column(
        SQLEnum(
            PublishingStatus,
            name="publishing_status_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=PublishingStatus.PUBLICADO,
        doc="Lifecycle status.",
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="UTC timestamp of publication.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    institution: Mapped[Institution] = relationship(
        "Institution",
        lazy="selectin",
    )
    author: Mapped[User] = relationship(
        "User",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<InstitutionalNews id={self.id} inst={self.institution_id} "
            f"title={self.title!r} category={self.category}>"
        )
