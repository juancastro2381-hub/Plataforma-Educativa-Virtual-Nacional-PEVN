"""
PEVN Backend — Technical Incident & Support Case Domain Model

Represents platform-level technical support tickets, service incidents,
and operational diagnostic cases managed by SUPER_ADMIN (Level 100).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class TechnicalIncidentSeverity(StrEnum):
    """Severity classification for technical operations incidents."""

    CRITICAL = "CRITICAL"  # System outage, data integrity risk, active security exploit
    HIGH = "HIGH"          # Degradation in core services (auth, database latency)
    MEDIUM = "MEDIUM"      # Non-critical functionality defect or performance advisory
    LOW = "LOW"            # Diagnostic inquiry, minor operational advisory


class TechnicalIncidentStatus(StrEnum):
    """Lifecycle state of technical support cases."""

    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    MITIGATED = "MITIGATED"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class TechnicalIncidentCategory(StrEnum):
    """Categorization for platform operational issues."""

    CONNECTIVITY = "CONNECTIVITY"
    DATABASE = "DATABASE"
    AUTHENTICATION = "AUTHENTICATION"
    INTEGRATION = "INTEGRATION"
    SECURITY = "SECURITY"
    PROVISIONING = "PROVISIONING"
    SYSTEM = "SYSTEM"


class TechnicalIncident(Base):
    """
    Technical Support Case / Platform Incident Record.

    Stores audit-traceable technical operational cases handled by the platform operator.
    Guarantees that sensitive user credentials or student personal data are NEVER stored.
    """

    __tablename__ = "technical_support_cases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    ticket_number: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        unique=True,
        index=True,
        doc="Human-readable ticket identifier (e.g. INC-2026-0001).",
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Summary title of the technical issue.",
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=TechnicalIncidentCategory.SYSTEM.value,
        index=True,
        doc="Technical category of the case.",
    )
    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TechnicalIncidentSeverity.MEDIUM.value,
        index=True,
        doc="Operational severity level.",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=TechnicalIncidentStatus.OPEN.value,
        index=True,
        doc="Current incident lifecycle status.",
    )
    affected_service: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="platform",
        doc="Service or subsystem affected (e.g. api, database, auth, redis).",
    )
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Associated institutional tenant context, if applicable.",
    )
    reporter_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Operator or user who logged the technical case.",
    )
    assigned_operator: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Name or email of the assigned technical operator.",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Sanitized technical description of the incident.",
    )
    technical_context: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=True,
        doc="Sanitized technical telemetry / error context (no secrets/passwords).",
    )
    resolution_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Operational mitigation and resolution documentation.",
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
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when the incident was marked RESOLVED or CLOSED.",
    )

    __table_args__ = (
        Index("ix_technical_cases_status_severity", "status", "severity"),
    )
