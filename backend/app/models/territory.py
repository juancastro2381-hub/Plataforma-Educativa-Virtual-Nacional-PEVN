"""
PEVN Backend — Territorial Domain Models (Departments & Municipalities)

Represents Colombian territorial divisions (DANE taxonomy) for
administrative scoping and hierarchical authority.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.institution import Institution


class Department(Base):
    """
    Colombian Department (Departamento).

    Top-level subnational territorial entity.
    Identified by official 2-digit DANE code (e.g. "05" for Antioquia).
    """

    __tablename__ = "departments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    code: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        nullable=False,
        index=True,
        doc="Official DANE 2-digit department code.",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Department name.",
    )

    # Relationships
    municipalities: Mapped[list[Municipality]] = relationship(
        "Municipality",
        back_populates="department",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Department code={self.code!r} name={self.name!r}>"


class Municipality(Base):
    """
    Colombian Municipality (Municipio).

    Second-level subnational territorial entity under a Department.
    Identified by official 5-digit DANE code (e.g. "05001" for Medellín).
    """

    __tablename__ = "municipalities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Parent department foreign key.",
    )
    code: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        nullable=False,
        index=True,
        doc="Official DANE 5-digit municipality code.",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Municipality name.",
    )

    # Relationships
    department: Mapped[Department] = relationship(
        "Department",
        back_populates="municipalities",
        lazy="selectin",
    )
    institutions: Mapped[list[Institution]] = relationship(
        "Institution",
        back_populates="municipality",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Municipality code={self.code!r} name={self.name!r}>"
