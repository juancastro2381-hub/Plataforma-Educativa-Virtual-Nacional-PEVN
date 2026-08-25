"""
PEVN Backend — Knowledge Area & Subject Domain Models

Represents Colombian curriculum areas (Áreas Fundamentales y Obligatorias)
and institution-specific subjects (Asignaturas) per grade level.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    SmallInteger,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.grade import Grade
    from app.models.institution import Institution


class KnowledgeArea(Base):
    """
    Knowledge Area Entity (Área Fundamental del Conocimiento).

    Represents curricular knowledge groupings according to Ley 115 de 1994
    (e.g., Matemáticas, Humanidades, Ciencias Naturales).
    institution_id is NULL for official MEN national areas, or set for custom
    institution-specific complementary areas.
    """

    __tablename__ = "knowledge_areas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
        doc="Null for national standard areas; non-null for custom institution areas.",
    )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        doc="Area name (e.g. 'Matemáticas y Razonamiento Lógico').",
    )
    is_mandatory: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether this area is statutory under national education guidelines.",
    )

    # Relationships
    subjects: Mapped[list[Subject]] = relationship(
        "Subject",
        back_populates="knowledge_area",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<KnowledgeArea name={self.name!r} institution_id={self.institution_id}>"
        )


class Subject(Base):
    """
    Curricular Subject Entity (Asignatura).

    Specific subject taught at an Educational Institution within a Grade level
    and Knowledge Area (e.g. 'Álgebra', 'Biología Celular', 'Lengua Castellana').
    """

    __tablename__ = "subjects"
    __table_args__ = (
        UniqueConstraint(
            "institution_id",
            "grade_id",
            "name",
            name="uq_subjects_institution_grade_name",
        ),
        CheckConstraint(
            "weekly_hours > 0",
            name="ck_subjects_weekly_hours",
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
    knowledge_area_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_areas.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Parent curricular knowledge area.",
    )
    grade_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("grades.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Target grade level from the national catalog.",
    )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        doc="Subject name (e.g. 'Geometría y Trigonometría').",
    )
    weekly_hours: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=4,
        doc="Weekly teaching hours (intensidad horaria semanal).",
    )

    # Relationships
    institution: Mapped[Institution] = relationship(
        "Institution",
        lazy="selectin",
    )
    knowledge_area: Mapped[KnowledgeArea] = relationship(
        "KnowledgeArea",
        back_populates="subjects",
        lazy="selectin",
    )
    grade: Mapped[Grade] = relationship(
        "Grade",
        back_populates="subjects",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<Subject name={self.name!r} institution_id={self.institution_id} "
            f"grade_id={self.grade_id}>"
        )
