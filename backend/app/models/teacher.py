"""
PEVN Backend — Teacher Domain Model

Extends User identity with educational and professional attributes for educators,
preserving institutional tenancy and professional ranking (escalafón).
"""

from __future__ import annotations

import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy import (
    ForeignKey,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.group import Group
    from app.models.institution import Institution
    from app.models.user import User


class TeacherContractType(enum.StrEnum):
    """
    Colombian Public Sector Teacher Appointment Types.
    """

    PROPIEDAD = "PROPIEDAD"  # Nombramiento en Carrera Docente
    PROVISIONAL = "PROVISIONAL"  # Nombramiento Provisional
    TEMPORAL = "TEMPORAL"  # Contrato por Horas Cátedra / Reemplazo


class Teacher(Base):
    """
    Teacher Profile Entity (Docente).

    Domain educational profile extending the central User account.
    """

    __tablename__ = "teachers"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            name="uq_teachers_user_id",
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
        doc="Affiliated Educational Institution (Tenant boundary).",
    )
    specialty_area: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
        doc="Pedagogical specialization (e.g. 'Licenciatura en Matemáticas').",
    )
    escalafon_grade: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Official teacher salary grade (e.g. '14', '2A', '3C').",
    )
    contract_type: Mapped[TeacherContractType] = mapped_column(
        SQLEnum(
            TeacherContractType,
            name="teacher_contract_type_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=TeacherContractType.PROPIEDAD,
        doc="Employment category.",
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
    directed_groups: Mapped[list[Group]] = relationship(
        "Group",
        back_populates="group_director",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<Teacher id={self.id} user_id={self.user_id} "
            f"institution_id={self.institution_id}>"
        )
