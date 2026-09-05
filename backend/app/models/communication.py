"""
PEVN Backend — Institutional Communications & Read Receipts Domain Models (Phase 15)

Official directives, circulars, meeting notices, target audiences, and unforgeable
read/acknowledgment receipts according to institutional governance rules.
"""

from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.grade import Grade
    from app.models.group import Group
    from app.models.institution import Campus, Institution
    from app.models.user import User


class CommunicationCategory(enum.StrEnum):
    """
    Official classification of institutional communications.
    """

    CIRCULAR_OFICIAL = "CIRCULAR_OFICIAL"
    CONVOCATORIA_REUNION = "CONVOCATORIA_REUNION"
    AVISO_ACADEMICO = "AVISO_ACADEMICO"
    AVISO_ADMINISTRATIVO = "AVISO_ADMINISTRATIVO"
    RECORDATORIO = "RECORDATORIO"
    EMERGENCIA_INSTITUCIONAL = "EMERGENCIA_INSTITUCIONAL"


class CommunicationPriority(enum.StrEnum):
    """
    Urgency priority level for delivery, badge highlighting, and notifications.
    """

    BAJA = "BAJA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    URGENTE = "URGENTE"


class TargetScopeType(enum.StrEnum):
    """
    Audience scope defining the recipient community boundary.
    """

    TODOS_INSTITUCION = "TODOS_INSTITUCION"
    SOLO_ESTUDIANTES = "SOLO_ESTUDIANTES"
    SOLO_ACUDIENTES = "SOLO_ACUDIENTES"
    SOLO_DOCENTES = "SOLO_DOCENTES"
    POR_SEDE = "POR_SEDE"
    POR_GRADO = "POR_GRADO"
    POR_GRUPO = "POR_GRUPO"


class PublishingStatus(enum.StrEnum):
    """
    Lifecycle status of institutional content.
    """

    BORRADOR = "BORRADOR"
    PUBLICADO = "PUBLICADO"
    ARCHIVADO = "ARCHIVADO"


class InstitutionalCommunication(Base):
    """
    Institutional Communication Entity (Comunicado / Circular Oficial).

    Represents formal institutional notices issued by Rectors, Coordinators,
    or administrative authorities with audience targeting, expiration, and read-receipts.
    """

    __tablename__ = "institutional_communications"

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
        doc="User who drafted or published the communication.",
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Official subject/title of the communication.",
    )
    summary: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        doc="Executive summary or teaser text.",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Full communication content (supports secure Markdown).",
    )
    category: Mapped[CommunicationCategory] = mapped_column(
        SQLEnum(
            CommunicationCategory,
            name="communication_category_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=CommunicationCategory.CIRCULAR_OFICIAL,
        doc="Official category.",
    )
    priority: Mapped[CommunicationPriority] = mapped_column(
        SQLEnum(
            CommunicationPriority,
            name="communication_priority_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=CommunicationPriority.MEDIA,
        doc="Delivery urgency level.",
    )
    target_scope: Mapped[TargetScopeType] = mapped_column(
        SQLEnum(
            TargetScopeType,
            name="target_scope_type_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=TargetScopeType.TODOS_INSTITUCION,
        doc="Target community boundary.",
    )
    attachment_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Optional URL/path to an official PDF circular document.",
    )
    requires_acknowledgment: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether recipients must explicitly acknowledge receipt.",
    )
    status: Mapped[PublishingStatus] = mapped_column(
        SQLEnum(
            PublishingStatus,
            name="publishing_status_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=PublishingStatus.PUBLICADO,
        doc="Publishing status.",
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="UTC timestamp of publication.",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        doc="Optional UTC expiration timestamp for active feeds (DECISION-15-02).",
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
    audiences: Mapped[list[CommunicationAudience]] = relationship(
        "CommunicationAudience",
        back_populates="communication",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    receipts: Mapped[list[CommunicationReceipt]] = relationship(
        "CommunicationReceipt",
        back_populates="communication",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def is_expired(self) -> bool:
        """Check whether the communication has passed its expiration timestamp."""
        if self.expires_at is None:
            return False
        if self.expires_at.tzinfo is not None:
            now = datetime.now(self.expires_at.tzinfo)
        else:
            now = datetime.now(UTC).replace(tzinfo=None)
        return now >= self.expires_at

    @property
    def is_active(self) -> bool:
        """Active if published and not expired."""
        return self.status == PublishingStatus.PUBLICADO and not self.is_expired

    def __repr__(self) -> str:
        return (
            f"<InstitutionalCommunication id={self.id} inst={self.institution_id} "
            f"title={self.title!r} status={self.status}>"
        )


class CommunicationAudience(Base):
    """
    Audience Targeting Linkage.

    Allows granular targeting by campus (sede), grade, group, or system role.
    """

    __tablename__ = "communication_audiences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    communication_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutional_communications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    campus_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campuses.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Target campus / sede.",
    )
    grade_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("grades.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Target curricular grade.",
    )
    group_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Target group / class section.",
    )
    role_name: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        doc="Target system role ('student', 'guardian', 'teacher').",
    )

    # Relationships
    communication: Mapped[InstitutionalCommunication] = relationship(
        "InstitutionalCommunication",
        back_populates="audiences",
        lazy="selectin",
    )
    campus: Mapped[Campus | None] = relationship(
        "Campus",
        lazy="selectin",
    )
    grade: Mapped[Grade | None] = relationship(
        "Grade",
        lazy="selectin",
    )
    group: Mapped[Group | None] = relationship(
        "Group",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<CommunicationAudience id={self.id} comm={self.communication_id} "
            f"group={self.group_id} role={self.role_name}>"
        )


class CommunicationReceipt(Base):
    """
    Read and Acknowledgment Receipt Record.

    Tracks when a recipient reads and formally acknowledges an institutional communication.
    Guarantees idempotency and unforgeable timestamp/IP logging.
    """

    __tablename__ = "communication_receipts"
    __table_args__ = (
        UniqueConstraint(
            "communication_id",
            "user_id",
            name="uq_communication_receipts_user",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    communication_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutional_communications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Recipient User identity who accessed or acknowledged.",
    )
    read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="UTC timestamp when the user first viewed the communication.",
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="UTC timestamp when the user explicitly confirmed receipt.",
    )
    client_ip: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Client IP address recorded at the time of acknowledgment.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    communication: Mapped[InstitutionalCommunication] = relationship(
        "InstitutionalCommunication",
        back_populates="receipts",
        lazy="selectin",
    )
    user: Mapped[User] = relationship(
        "User",
        lazy="selectin",
    )

    @property
    def is_acknowledged(self) -> bool:
        """Check whether receipt has been acknowledged."""
        return self.acknowledged_at is not None

    def __repr__(self) -> str:
        return (
            f"<CommunicationReceipt id={self.id} comm={self.communication_id} "
            f"user={self.user_id} ack={self.is_acknowledged}>"
        )
