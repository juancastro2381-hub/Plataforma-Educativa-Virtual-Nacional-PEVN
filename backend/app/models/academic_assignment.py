"""
PEVN Backend — Academic Assignment Domain Model

Represents teacher workload allocation (Carga Académica Docente) binding an educator
to a subject and classroom group for an academic school year.
Enforces single active teacher assignment per (subject, group, year) via
PostgreSQL partial unique index while preserving historical inactive assignments.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    SmallInteger,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.academic_year import AcademicYear
    from app.models.group import Group
    from app.models.subject import Subject
    from app.models.teacher import Teacher


class AcademicAssignment(Base):
    """
    Academic Assignment Entity (Carga Académica / Asignación Docente).

    Binds a teacher to teach a subject within a specific group section
    during an academic year.
    """

    __tablename__ = "academic_assignments"
    __table_args__ = (
        Index(
            "uq_academic_assignments_single_active",
            "subject_id",
            "group_id",
            "academic_year_id",
            unique=True,
            postgresql_where=text("is_active = true"),
            sqlite_where=text("is_active = 1"),
        ),
        Index(
            "ix_academic_assignments_lookup",
            "teacher_id",
            "academic_year_id",
        ),
        CheckConstraint(
            "weekly_hours > 0",
            name="ck_academic_assignments_weekly_hours",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teachers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Assigned educator.",
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Subject being taught.",
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
        doc="Associated school year.",
    )
    weekly_hours: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        doc="Weekly teaching hours assigned to this teacher.",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether this teacher is the current active instructor for this class.",
    )

    # Relationships
    teacher: Mapped[Teacher] = relationship(
        "Teacher",
        lazy="selectin",
    )
    subject: Mapped[Subject] = relationship(
        "Subject",
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

    def __repr__(self) -> str:
        return (
            f"<AcademicAssignment id={self.id} teacher_id={self.teacher_id} "
            f"subject_id={self.subject_id} group_id={self.group_id} "
            f"is_active={self.is_active}>"
        )
