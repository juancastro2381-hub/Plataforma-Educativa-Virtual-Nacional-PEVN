"""
PEVN Backend — Group / Course Domain Model

Represents class sections (Cursos / Salones) physically hosted in a Campus (Sede),
associated with a Grade level, Academic Year, school shift (Jornada), and capacity.
"""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
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
    from app.models.academic_year import AcademicYear
    from app.models.grade import Grade
    from app.models.institution import Campus
    from app.models.teacher import Teacher


class ShiftEnum(enum.StrEnum):
    """
    Colombian Educational Shift Types (Jornadas Escolares).
    """

    MANANA = "MANANA"  # Jornada Mañana
    TARDE = "TARDE"  # Jornada Tarde
    NOCHE = "NOCHE"  # Jornada Nocturna (Educación de Adultos)
    UNICA = "UNICA"  # Jornada Única (Decreto 501 de 2016)
    SABATINA = "SABATINA"  # Jornada Sabatina / Fin de Semana


class Group(Base):
    """
    Class Group / Section Entity (Grupo o Salón de Clases).

    Scoped by Campus, AcademicYear, Grade level, and operational shift.
    """

    __tablename__ = "groups"
    __table_args__ = (
        UniqueConstraint(
            "campus_id",
            "academic_year_id",
            "grade_id",
            "name",
            name="uq_groups_campus_year_grade_name",
        ),
        CheckConstraint(
            "capacity_limit > 0",
            name="ck_groups_capacity_positive",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    campus_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campuses.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Host Campus (Sede Educativa) - Tenant sub-boundary.",
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Associated school year.",
    )
    grade_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("grades.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Standardized national grade level.",
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Group section identifier (e.g. '10-01', '10-A').",
    )
    shift: Mapped[ShiftEnum] = mapped_column(
        SQLEnum(
            ShiftEnum,
            name="shift_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=ShiftEnum.MANANA,
        doc="School shift.",
    )
    capacity_limit: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=40,
        doc="Maximum student enrollment capacity.",
    )
    group_director_teacher_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Assigned Group Director Teacher.",
    )

    # Relationships
    campus: Mapped[Campus] = relationship(
        "Campus",
        lazy="selectin",
    )
    academic_year: Mapped[AcademicYear] = relationship(
        "AcademicYear",
        lazy="selectin",
    )
    grade: Mapped[Grade] = relationship(
        "Grade",
        lazy="selectin",
    )
    group_director: Mapped[Teacher | None] = relationship(
        "Teacher",
        foreign_keys=[group_director_teacher_id],
        back_populates="directed_groups",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<Group name={self.name!r} campus_id={self.campus_id} "
            f"grade_id={self.grade_id} shift={self.shift}>"
        )
