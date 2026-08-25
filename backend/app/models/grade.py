"""
PEVN Backend — Standardized Grade Domain Model

Represents the Colombian national curriculum grade levels (Preescolar, Primaria,
Secundaria, Media) regulated by the Ministerio de Educación Nacional (MEN).

NOTE: Grade is a SHARED NATIONAL CATALOG. It intentionally does NOT contain
institution_id, ensuring nationwide curriculum standardization.
"""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy import (
    SmallInteger,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.subject import Subject


class EducationalLevel(enum.StrEnum):
    """
    Colombian Educational System Levels (Ley 115 de 1994).
    """

    PREESCOLAR = "PREESCOLAR"  # Grados Transición / 00
    PRIMARIA = "PRIMARIA"  # Grados 1° a 5°
    SECUNDARIA = "SECUNDARIA"  # Grados 6° a 9°
    MEDIA = "MEDIA"  # Grados 10° y 11°


class Grade(Base):
    """
    Standardized Academic Grade Entity (Grado Escolar).

    Global reference catalog across all Colombian public institutions.
    """

    __tablename__ = "grades"
    __table_args__ = (
        UniqueConstraint(
            "code",
            name="uq_grades_code",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        doc="Standardized national grade code (e.g. 'TRANSICION', 'G01', 'G10').",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Display name (e.g. 'Transición', 'Grado Décimo').",
    )
    level: Mapped[EducationalLevel] = mapped_column(
        SQLEnum(
            EducationalLevel,
            name="educational_level_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        doc="Educational stage (Preescolar, Primaria, Secundaria, Media).",
    )
    ordinal_order: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        doc="Sequential progression index (0 for Transición, 1..11).",
    )

    # Relationships
    subjects: Mapped[list[Subject]] = relationship(
        "Subject",
        back_populates="grade",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Grade code={self.code!r} name={self.name!r} level={self.level}>"
