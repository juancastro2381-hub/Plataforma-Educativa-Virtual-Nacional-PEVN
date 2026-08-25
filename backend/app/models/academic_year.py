"""
PEVN Backend — Academic Year & Academic Period Domain Models

Represents annual school calendars (Calendario A / B), operational states,
and evaluative term divisions (periods) for educational institutions.
"""

from __future__ import annotations

import enum
import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
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

if TYPE_CHECKING:
    from app.models.institution import Institution


class AcademicYearCalendarType(enum.StrEnum):
    """
    Colombian Educational Calendar Types.
    """

    CALENDAR_A = "CALENDAR_A"  # Febrero a Noviembre
    CALENDAR_B = "CALENDAR_B"  # Septiembre a Junio


class AcademicYearStatus(enum.StrEnum):
    """
    Academic Year Lifecycle States.
    """

    PLANNING = "PLANNING"  # Configuración inicial de períodos y grupos
    ACTIVE = "ACTIVE"  # Año escolar en curso
    CLOSED = "CLOSED"  # Calificaciones cerradas y promoción procesada
    ARCHIVED = "ARCHIVED"  # Registro histórico inmutable


class AcademicYear(Base):
    """
    Academic Year Entity (Año Lectivo).

    Represents a specific school year within an Educational Institution (Tenant).
    Only one AcademicYear may be ACTIVE simultaneously per institution.
    """

    __tablename__ = "academic_years"
    __table_args__ = (
        UniqueConstraint(
            "institution_id",
            "year",
            name="uq_academic_years_institution_year",
        ),
        Index(
            "ix_academic_years_institution_status",
            "institution_id",
            "status",
        ),
        CheckConstraint(
            "start_date < end_date",
            name="ck_academic_years_date_order",
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
        doc="Owning educational institution (Tenant boundary).",
    )
    year: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        doc="School calendar year (e.g. 2026).",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Display name (e.g. 'Año Escolar 2026').",
    )
    calendar_type: Mapped[AcademicYearCalendarType] = mapped_column(
        SQLEnum(
            AcademicYearCalendarType,
            name="academic_calendar_type_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=AcademicYearCalendarType.CALENDAR_A,
        doc="Colombian academic calendar type (A or B).",
    )
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Official start date of the academic year.",
    )
    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Official closing date of the academic year.",
    )
    status: Mapped[AcademicYearStatus] = mapped_column(
        SQLEnum(
            AcademicYearStatus,
            name="academic_year_status_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=AcademicYearStatus.PLANNING,
        doc="Operational state of the academic year.",
    )

    # Relationships
    institution: Mapped[Institution] = relationship(
        "Institution",
        lazy="selectin",
    )
    periods: Mapped[list[AcademicPeriod]] = relationship(
        "AcademicPeriod",
        back_populates="academic_year",
        cascade="all, delete-orphan",
        order_by="AcademicPeriod.period_number",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<AcademicYear year={self.year} institution_id={self.institution_id} "
            f"status={self.status}>"
        )


class AcademicPeriod(Base):
    """
    Academic Evaluation Period (Período Académico).

    Subdivision of an AcademicYear for grade evaluation terms.
    The sum of period weights within an academic year must equal 100%.
    """

    __tablename__ = "academic_periods"
    __table_args__ = (
        UniqueConstraint(
            "academic_year_id",
            "period_number",
            name="uq_academic_periods_year_number",
        ),
        CheckConstraint(
            "weight_percentage > 0 AND weight_percentage <= 100",
            name="ck_academic_periods_weight",
        ),
        CheckConstraint(
            "start_date < end_date",
            name="ck_academic_periods_date_order",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent academic year.",
    )
    period_number: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        doc="Sequential period index within the year (1, 2, 3, 4).",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Display name (e.g. 'Primer Período').",
    )
    weight_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        doc="Evaluation weight percentage (e.g. 25.00 for 25%).",
    )
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Term start date.",
    )
    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Term end date.",
    )
    is_closed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether grade entries for this period are locked.",
    )

    # Relationships
    academic_year: Mapped[AcademicYear] = relationship(
        "AcademicYear",
        back_populates="periods",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<AcademicPeriod period_number={self.period_number} "
            f"name={self.name!r} weight={self.weight_percentage}%>"
        )
