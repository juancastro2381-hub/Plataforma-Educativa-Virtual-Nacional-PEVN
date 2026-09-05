"""
PEVN Backend — Enrollment and Group Transfer History Domain Models

Represents student enrollment (Matrícula) in groups per academic year,
enforcing single active enrollment per year via PostgreSQL partial unique indexes,
and immutable group transfer audit trail.
"""

from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
    text,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.academic_year import AcademicYear
    from app.models.group import Group
    from app.models.student import Student
    from app.models.user import User


class EnrollmentStatus(enum.StrEnum):
    """
    Student Enrollment Lifecycle Statuses.
    """

    PRE_ENROLLED = "PRE_ENROLLED"  # Prematrícula / Asignación de cupo
    ACTIVE = "ACTIVE"  # Matrícula activa regular
    WITHDRAWN = "WITHDRAWN"  # Retirado (Deserción / Cancelación)
    TRANSFERRED = "TRANSFERRED"  # Trasladado a otro grupo o I.E.
    GRADUATED = "GRADUATED"  # Graduado (completed school cycle - ONLY for Grade 11 / Grado 11 completers)


class Enrollment(Base):
    """
    Student Enrollment Entity (Matrícula Académica).

    Binds a student to an educational group for a specific academic year.
    Enforces the mandatory invariant: A student may only have ONE ACTIVE
    enrollment per academic year via PostgreSQL partial unique index.
    """

    __tablename__ = "enrollments"
    __table_args__ = (
        Index(
            "uq_enrollments_single_active_per_year",
            "student_id",
            "academic_year_id",
            unique=True,
            postgresql_where=text("status = 'ACTIVE'"),
            sqlite_where=text("status = 'ACTIVE'"),
        ),
        Index(
            "ix_enrollments_tenant_query",
            "academic_year_id",
            "group_id",
            "status",
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
        ForeignKey("students.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Enrolled student.",
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Target classroom group section.",
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Target academic school year.",
    )
    enrollment_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
        doc="Date the enrollment contract was signed.",
    )
    status: Mapped[EnrollmentStatus] = mapped_column(
        SQLEnum(
            EnrollmentStatus,
            name="enrollment_status_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=EnrollmentStatus.ACTIVE,
        doc="Enrollment lifecycle status.",
    )
    status_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Audit justification for status transitions (e.g. reason for withdrawal).",
    )

    # Relationships
    student: Mapped[Student] = relationship(
        "Student",
        lazy="selectin",
    )
    group: Mapped[Group] = relationship(
        "Group",
        lazy="selectin",
    )
    academic_year: Mapped[AcademicYear] = relationship(
        "AcademicYear",
        lazy="selectin",
    )
    transfer_history: Mapped[list[GroupTransferHistory]] = relationship(
        "GroupTransferHistory",
        back_populates="enrollment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<Enrollment id={self.id} student_id={self.student_id} "
            f"group_id={self.group_id} status={self.status}>"
        )


class GroupTransferHistory(Base):
    """
    Group Transfer History Entity (Trazabilidad de Traslados de Salón).

    Immutable audit trail recording student classroom and shift reassignments.
    """

    __tablename__ = "group_transfer_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("enrollments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Parent enrollment record.",
    )
    previous_group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Origin classroom group.",
    )
    new_group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Destination classroom group.",
    )
    transferred_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Administrator/Coordinator who authorized the transfer.",
    )
    transfer_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now,
        server_default=func.now(),
        doc="Timestamp of the transfer event.",
    )
    reason: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Administrative justification for the transfer.",
    )

    # Relationships
    enrollment: Mapped[Enrollment] = relationship(
        "Enrollment",
        back_populates="transfer_history",
        lazy="selectin",
    )
    previous_group: Mapped[Group] = relationship(
        "Group",
        foreign_keys=[previous_group_id],
        lazy="selectin",
    )
    new_group: Mapped[Group] = relationship(
        "Group",
        foreign_keys=[new_group_id],
        lazy="selectin",
    )
    transferred_by: Mapped[User] = relationship(
        "User",
        foreign_keys=[transferred_by_user_id],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<GroupTransferHistory enrollment_id={self.enrollment_id} "
            f"from={self.previous_group_id} to={self.new_group_id}>"
        )
