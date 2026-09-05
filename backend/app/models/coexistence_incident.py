"""
PEVN Backend — School Coexistence & Student Incidents Domain Models (Phase 15)

Implements the official "Observador del Estudiante" and School Coexistence framework
aligned with Colombian Ley 1620 de 2013 and Decreto 1965 de 2013.
Guarantees strict confidentiality, due process, and Anti-IDOR family isolation.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
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

if TYPE_CHECKING:
    from app.models.institution import Institution
    from app.models.student import Student
    from app.models.user import User


class CoexistenceSituationType(enum.StrEnum):
    """
    Classification of school coexistence situations according to Colombian Ley 1620 de 2013.
    """

    TIPO_I = "TIPO_I"  # Situaciones de manejo pedagógico interno / conflictos esporádicos
    TIPO_II = "TIPO_II"  # Acoso escolar (bullying), ciberacoso o agresiones sin incapacidad
    TIPO_III = "TIPO_III"  # Situaciones presuntamente constitutivas de delito o daños graves
    OBSERVACION_POSITIVA = "OBSERVACION_POSITIVA"  # Felicitación, liderazgo, mérito convivencial


class IncidentStatus(enum.StrEnum):
    """
    Progress lifecycle status of a student coexistence situation.
    """

    ABIERTO = "ABIERTO"
    EN_SEGUIMIENTO = "EN_SEGUIMIENTO"
    CON_COMPROMISOS = "CON_COMPROMISOS"
    CERRADO = "CERRADO"


class StudentIncident(Base):
    """
    Student Coexistence Incident Entity (Observador del Estudiante / Situación Convivencial).

    Confidential record documenting behavioral observations, due-process hearing,
    pedagogical commitments, and legal coexistence situation handling.
    """

    __tablename__ = "student_incidents"

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
        doc="Educational institution tenant boundary.",
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Enrolled student whose file is being documented.",
    )
    reporter_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Teacher, Coordinator, or Rector who authored the record.",
    )
    situation_type: Mapped[CoexistenceSituationType] = mapped_column(
        SQLEnum(
            CoexistenceSituationType,
            name="coexistence_situation_type_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=CoexistenceSituationType.TIPO_I,
        doc="Official Ley 1620 situation category.",
    )
    incident_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="UTC date and time when the facts occurred.",
    )
    location: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        doc="Physical or virtual environment (e.g. 'Aula 10-A', 'Patio Central', 'Clase Virtual').",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Objective report of the observed facts.",
    )
    student_version: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Student's testimony / due-process statement (descargos).",
    )
    pedagogical_measures: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Restorative pedagogical actions, guidance, or counseling assigned.",
    )
    commitments: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Explicit commitments agreed upon by student, family, and educator.",
    )
    status: Mapped[IncidentStatus] = mapped_column(
        SQLEnum(
            IncidentStatus,
            name="incident_status_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=IncidentStatus.ABIERTO,
        doc="Lifecycle status.",
    )
    is_visible_to_guardian: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether authorized legal guardians may view this entry in their portal.",
    )
    is_visible_to_student: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether the student may view this entry in their portal (DECISION-15-01).",
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="UTC timestamp when the situation was resolved and closed.",
    )
    closed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        doc="User who approved closure.",
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
    student: Mapped[Student] = relationship(
        "Student",
        lazy="selectin",
    )
    reporter: Mapped[User] = relationship(
        "User",
        foreign_keys=[reporter_user_id],
        lazy="selectin",
    )
    closed_by: Mapped[User | None] = relationship(
        "User",
        foreign_keys=[closed_by_user_id],
        lazy="selectin",
    )
    follow_ups: Mapped[list[IncidentFollowUp]] = relationship(
        "IncidentFollowUp",
        back_populates="incident",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<StudentIncident id={self.id} student_id={self.student_id} "
            f"type={self.situation_type} status={self.status}>"
        )


class IncidentFollowUp(Base):
    """
    Incident Follow-Up Log Entry.

    Chronological tracking of agreements, psychological counseling sessions,
    and parental interviews regarding a coexistence incident.
    """

    __tablename__ = "incident_follow_ups"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="User who conducted this follow-up session.",
    )
    follow_up_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="Date and time of the follow-up encounter.",
    )
    notes: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Detailed observations and progress noted.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    incident: Mapped[StudentIncident] = relationship(
        "StudentIncident",
        back_populates="follow_ups",
        lazy="selectin",
    )
    author: Mapped[User] = relationship(
        "User",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<IncidentFollowUp id={self.id} incident_id={self.incident_id} "
            f"date={self.follow_up_date}>"
        )
