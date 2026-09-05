"""
PEVN Backend — Guardian and Student-Guardian Association Domain Models

Represents legal guardians (Acudientes / Padres / Tutores) and their relationships
with enrolled students, respecting [OPEN-DECISION-3A-01] where guardians may be
identified via National ID without requiring a mandatory unique email or user account.
"""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    ForeignKey,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.user import DocumentType

if TYPE_CHECKING:
    from app.models.institution import Institution
    from app.models.student import Student
    from app.models.user import User


class GuardianRelationshipType(enum.StrEnum):
    """
    Kinship / Legal Representation Categories.
    """

    PADRE = "PADRE"
    MADRE = "MADRE"
    ABUELO_A = "ABUELO_A"
    TIO_A = "TIO_A"
    TUTOR_LEGAL = "TUTOR_LEGAL"
    OTRO = "OTRO"


class Guardian(Base):
    """
    Guardian Entity (Acudiente / Representante Legal).

    Holds civil identity and emergency contact information for student guardians.
    user_id is optional: rural or offline guardians do not require a login account.
    institution_id enforces strict multi-tenant boundary per educational establishment.
    """

    __tablename__ = "guardians"
    __table_args__ = (
        UniqueConstraint(
            "institution_id",
            "document_type",
            "document_number",
            name="uq_guardians_institution_document",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Educational institution tenant boundary.",
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        unique=True,
        nullable=True,
        index=True,
        doc="Optional 1:1 link to User if the guardian has platform login access.",
    )
    document_type: Mapped[DocumentType] = mapped_column(
        SQLEnum(
            DocumentType,
            name="document_type_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=DocumentType.CC,
        doc="Identity document type.",
    )
    document_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Official identity document number.",
    )
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="First name.",
    )
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Last name.",
    )
    phone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Primary telephone / mobile number for urgent contact.",
    )
    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Email address (optional per OPEN-DECISION-3A-01).",
    )
    address: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Physical residence address.",
    )
    relationship_type: Mapped[GuardianRelationshipType] = mapped_column(
        SQLEnum(
            GuardianRelationshipType,
            name="guardian_relationship_type_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=GuardianRelationshipType.MADRE,
        doc="Kinship relationship to student.",
    )

    # Relationships
    institution: Mapped[Institution] = relationship(
        "Institution",
        lazy="selectin",
    )
    user: Mapped[User | None] = relationship(
        "User",
        lazy="selectin",
    )
    students: Mapped[list[StudentGuardian]] = relationship(
        "StudentGuardian",
        back_populates="guardian",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<Guardian id={self.id} inst={self.institution_id} "
            f"doc={self.document_type}:{self.document_number} "
            f"name={self.first_name} {self.last_name}>"
        )


class StudentGuardian(Base):
    """
    Student-Guardian Association Entity.

    Links students with their authorized legal guardians, contact priority,
    and student pickup authorizations.
    """

    __tablename__ = "student_guardians"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "guardian_id",
            name="uq_student_guardians_student_guardian",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Associated Student.",
    )
    guardian_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("guardians.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Associated Guardian.",
    )
    relationship_type: Mapped[GuardianRelationshipType] = mapped_column(
        SQLEnum(
            GuardianRelationshipType,
            name="guardian_relationship_type_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=GuardianRelationshipType.MADRE,
        doc="Specific kinship for this student.",
    )
    is_primary_contact: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Primary emergency call order.",
    )
    is_authorized_pickup: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Authorized to accompany student at dismissal.",
    )

    # Relationships
    student: Mapped[Student] = relationship(
        "Student",
        back_populates="guardians",
        lazy="selectin",
    )
    guardian: Mapped[Guardian] = relationship(
        "Guardian",
        back_populates="students",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<StudentGuardian student_id={self.student_id} "
            f"guardian_id={self.guardian_id} rel={self.relationship_type}>"
        )
