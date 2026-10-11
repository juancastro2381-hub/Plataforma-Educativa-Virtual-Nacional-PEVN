"""
PEVN Backend — Institution Onboarding Request Domain Model

Represents the formal provisioning lifecycle workflow transforming an official
establishment from official_institution_catalog into an operational PEVN tenant
with campuses and administrative authority.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.institution import Institution
    from app.models.official_catalog import OfficialInstitutionCatalog
    from app.models.territory import Department, Municipality
    from app.models.user import User


class OnboardingRequestStatus(StrEnum):
    """
    Formal lifecycle states for an institution onboarding request.
    """

    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    PROVISIONED = "PROVISIONED"


class InstitutionOnboardingRequest(Base):
    """
    Institution Onboarding Request (Solicitud de Aprovisionamiento Institucional).

    Governs the transition from an official Colombian educational catalog
    record (MEN / DANE) to an operational PEVN SaaS tenant.
    """

    __tablename__ = "institution_onboarding_requests"

    __table_args__ = (
        Index("uq_onboarding_request_number", "request_number", unique=True),
        Index("ix_onboarding_department_status", "department_id", "status"),
        Index("ix_onboarding_status_created", "status", "created_at"),
        Index("ix_onboarding_dane_code", "dane_code"),
        Index(
            "uq_onboarding_active_catalog_institution",
            "catalog_institution_id",
            unique=True,
            postgresql_where=text(
                "status IN ('DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'APPROVED')"
            ),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    request_number: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="Human-friendly unique filing code (e.g. ONB-2026-00042).",
    )
    catalog_institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("official_institution_catalog.id", ondelete="RESTRICT"),
        nullable=False,
        doc="Authoritative reference to official Colombian educational catalog establishment.",
    )
    dane_code: Mapped[str] = mapped_column(
        String(12),
        nullable=False,
        doc="Official 12-digit DANE institutional code.",
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False,
        doc="Territorial department jurisdiction.",
    )
    municipality_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("municipalities.id", ondelete="RESTRICT"),
        nullable=False,
        doc="Operational municipality of the principal campus.",
    )
    requested_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        doc="User filing the onboarding request.",
    )
    requester_role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Role of the requester at submission time.",
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default=OnboardingRequestStatus.SUBMITTED.value,
        server_default=text("'SUBMITTED'"),
        doc="Current state machine status.",
    )
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="SET NULL"),
        nullable=True,
        doc="Linked operational PEVN tenant upon successful provisioning.",
    )
    contact_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Official contact email designated for the tenant.",
    )
    contact_phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Official institutional contact phone number.",
    )
    proposed_rector_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Full name of proposed Rector for immediate invitation chaining.",
    )
    proposed_rector_email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Official email of proposed Rector.",
    )
    proposed_rector_doc_type: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        doc="Document type of proposed Rector (CC, CE).",
    )
    proposed_rector_doc_num: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Document number of proposed Rector.",
    )
    justification: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Administrative justification for the request.",
    )
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        doc="Technical reviewer assigned.",
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when technical review commenced.",
    )
    review_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Observations recorded during review.",
    )
    approved_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        doc="Authorizing administrative authority.",
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of approval.",
    )
    rejected_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        doc="Authority rejecting the request.",
    )
    rejected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of rejection.",
    )
    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Mandatory justification for administrative rejection.",
    )
    cancelled_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        doc="User who withdrew/cancelled the request.",
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of cancellation.",
    )
    cancellation_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Reason for withdrawal.",
    )
    provisioned_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        doc="Operator executing tenant provisioning.",
    )
    provisioned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of tenant creation.",
    )
    lock_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        doc="Optimistic locking version counter.",
    )
    idempotency_key: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        doc="Client-supplied idempotency key.",
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
    catalog_institution: Mapped[OfficialInstitutionCatalog] = relationship(
        "OfficialInstitutionCatalog",
        lazy="selectin",
    )
    department: Mapped[Department] = relationship(
        "Department",
        lazy="selectin",
    )
    municipality: Mapped[Municipality] = relationship(
        "Municipality",
        lazy="selectin",
    )
    requested_by: Mapped[User] = relationship(
        "User",
        foreign_keys=[requested_by_id],
        lazy="selectin",
    )
    institution: Mapped[Institution | None] = relationship(
        "Institution",
        foreign_keys=[institution_id],
        lazy="selectin",
    )
    reviewed_by: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[reviewed_by_id],
        lazy="selectin",
    )
    approved_by: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[approved_by_id],
        lazy="selectin",
    )
    rejected_by: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[rejected_by_id],
        lazy="selectin",
    )
    cancelled_by: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[cancelled_by_id],
        lazy="selectin",
    )
    provisioned_by: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[provisioned_by_id],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<InstitutionOnboardingRequest {self.request_number} "
            f"status={self.status} dane={self.dane_code}>"
        )
