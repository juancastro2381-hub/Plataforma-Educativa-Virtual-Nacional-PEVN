"""
PEVN Backend — Persistent Audit Log Domain Model

Provides immutable, append-only security event records for comprehensive auditability.
Guarantees that sensitive credentials (passwords, tokens, keys) are never stored.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.institution import Institution
    from app.models.user import User


class AuditLog(Base):
    """
    Audit Log Record.

    Stores tamper-evident records of all security-critical operations,
    logins, authorization decisions, and administrative changes.
    """

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Machine name of the event type (from AuditEventType).",
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="User UUID who triggered the event (NULL for anonymous/unauthenticated).",
    )
    actor_ip: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Client IP address of the actor.",
    )
    actor_user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="User-Agent header of the actor's request.",
    )
    target_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Identifier of the entity affected (user ID, institution ID, etc.).",
    )
    target_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Type of the entity affected (e.g. 'user', 'institution', 'role').",
    )
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Institution context for multi-tenant audit segregation.",
    )
    correlation_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        doc="Request correlation ID for tracing across microservices/logs.",
    )
    success: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether the audited action succeeded.",
    )
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=False,
        server_default=text("'{}'"),
        doc="Sanitized JSON metadata. Secrets are strictly stripped before saving.",
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="UTC timestamp when the event occurred.",
    )

    # Relationships
    actor: Mapped[User | None] = relationship(
        "User",
        lazy="selectin",
    )
    institution: Mapped[Institution | None] = relationship(
        "Institution",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id} event={self.event_type!r} "
            f"actor={self.actor_id} success={self.success}>"
        )
