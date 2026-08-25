"""
PEVN Backend — Student Domain Model

Extends User identity with academic, socio-demographic, and inclusion attributes
according to the Colombian Ministerio de Educación Nacional (MEN) and SIMAT standards.
"""

from __future__ import annotations

import enum
import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
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
    from app.models.guardian import StudentGuardian
    from app.models.institution import Institution
    from app.models.user import User


class StudentGender(enum.StrEnum):
    """
    Student Gender according to official Colombian civil registration.
    """

    M = "M"  # Masculino
    F = "F"  # Femenino
    OTRO = "OTRO"  # No binario / Otro


class Student(Base):
    """
    Student Profile Entity (Estudiante).

    Domain educational profile extending the central User account.
    """

    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            name="uq_students_user_id",
        ),
        UniqueConstraint(
            "code_simat",
            name="uq_students_code_simat",
        ),
        CheckConstraint(
            "stratum IS NULL OR (stratum >= 1 AND stratum <= 6)",
            name="ck_students_stratum_range",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
        index=True,
        doc="1:1 relationship with central User identity.",
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Enrolling Educational Institution (Tenant boundary).",
    )
    code_simat: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique National Student Code from SIMAT.",
    )
    birth_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Date of birth.",
    )
    gender: Mapped[StudentGender] = mapped_column(
        SQLEnum(
            StudentGender,
            name="student_gender_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=StudentGender.M,
        doc="Gender.",
    )
    blood_type: Mapped[str | None] = mapped_column(
        String(5),
        nullable=True,
        doc="Blood group & RH factor (e.g. 'O+', 'A-').",
    )
    stratum: Mapped[int | None] = mapped_column(
        SmallInteger,
        nullable=True,
        doc="Socio-economic stratum (1 to 6).",
    )
    eps_health_provider: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Health insurance provider (EPS).",
    )
    has_disability: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether the student is registered under educational inclusion programs.",
    )
    disability_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Type of disability or exceptional talent.",
    )

    # Relationships
    user: Mapped[User] = relationship(
        "User",
        lazy="selectin",
    )
    institution: Mapped[Institution] = relationship(
        "Institution",
        lazy="selectin",
    )
    guardians: Mapped[list[StudentGuardian]] = relationship(
        "StudentGuardian",
        back_populates="student",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<Student id={self.id} code_simat={self.code_simat!r} "
            f"institution_id={self.institution_id}>"
        )
