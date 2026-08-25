"""
PEVN Backend — Institutional Domain Models (Institutions & Campuses)

Represents educational institutions (Colegios / IED / IE) and their
physical or virtual campuses (sedes). Serves as tenant boundary.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.role import UserRole
    from app.models.territory import Municipality
    from app.models.user import User


class Institution(Base):
    """
    Educational Institution (Institución Educativa / Tenant).

    Primary tenant isolation boundary in PEVN.
    Identified by official 12-digit DANE institutional code.
    """

    __tablename__ = "institutions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    municipality_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("municipalities.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Municipality where the institution is located.",
    )
    dane_code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        doc="Official DANE 12-digit institutional code.",
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Official institution name.",
    )
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Institutional contact email.",
    )
    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Institutional contact phone number.",
    )
    address: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Physical address.",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether the institution is active in PEVN.",
    )

    # Relationships
    municipality: Mapped[Municipality] = relationship(
        "Municipality",
        back_populates="institutions",
        lazy="selectin",
    )
    campuses: Mapped[list[Campus]] = relationship(
        "Campus",
        back_populates="institution",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    users: Mapped[list[User]] = relationship(
        "User",
        back_populates="institution",
        lazy="selectin",
    )
    user_roles: Mapped[list[UserRole]] = relationship(
        "UserRole",
        back_populates="institution",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Institution dane_code={self.dane_code!r} name={self.name!r}>"


class Campus(Base):
    """
    Institution Campus (Sede Educativa).

    Physical or organizational subdivision of an institution.
    Identified by official DANE sede code.
    """

    __tablename__ = "campuses"

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
        doc="Parent institution foreign key.",
    )
    dane_sede_code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        doc="Official DANE sede code.",
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Campus name (e.g. Sede Principal, Sede B).",
    )
    address: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Campus physical address.",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether the campus is active.",
    )

    # Relationships
    institution: Mapped[Institution] = relationship(
        "Institution",
        back_populates="campuses",
        lazy="selectin",
    )
    user_roles: Mapped[list[UserRole]] = relationship(
        "UserRole",
        back_populates="campus",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Campus dane_sede_code={self.dane_sede_code!r} name={self.name!r}>"
