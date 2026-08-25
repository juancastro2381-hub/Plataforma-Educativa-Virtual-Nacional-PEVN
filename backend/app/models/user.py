"""
PEVN Backend — User Identity Domain Model

Represents registered users in the platform, incorporating security state,
lockout controls, identity document taxonomy, and institutional affiliation.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
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
    from app.models.role import UserRole
    from app.models.token import PasswordResetToken, RefreshToken


class DocumentType(enum.StrEnum):
    """
    Official Colombian Identity Document Types.
    """

    CC = "CC"  # Cédula de Ciudadanía
    TI = "TI"  # Tarjeta de Identidad (minors 7-17)
    CE = "CE"  # Cédula de Extranjería
    PEP = "PEP"  # Permiso Especial de Permanencia
    PPT = "PPT"  # Permiso por Protección Temporal
    PASSPORT = "PASSPORT"  # Pasaporte


class User(Base):
    """
    User Account Entity.

    Central identity table holding credential metadata, security lockout states,
    and institutional affiliation.
    """

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("document_type", "document_number", name="uq_users_document"),
    )

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
        doc="Primary institution affiliation (NULL for national administrators).",
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        doc="Primary unique email address used for login and notifications.",
    )
    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique username handle.",
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Argon2id cryptographic password hash. Never plaintext.",
    )
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="User first name(s).",
    )
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="User last name(s).",
    )
    document_type: Mapped[DocumentType] = mapped_column(
        SQLEnum(
            DocumentType,
            name="document_type_enum",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=DocumentType.CC,
        doc="Colombian identification document type.",
    )
    document_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Document number string.",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether the user account is enabled.",
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether the user email address has been verified.",
    )
    must_change_password: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Forces user to change password on next successful login.",
    )
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Consecutive failed login counter for brute-force lockout protection.",
    )
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Lockout expiration timestamp. Account is locked if locked_until > NOW().",
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of the most recent successful login.",
    )

    # Relationships
    institution: Mapped[Institution | None] = relationship(
        "Institution",
        back_populates="users",
        lazy="selectin",
    )
    user_roles: Mapped[list[UserRole]] = relationship(
        "UserRole",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    password_reset_tokens: Mapped[list[PasswordResetToken]] = relationship(
        "PasswordResetToken",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def full_name(self) -> str:
        """Return combined full name."""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_locked(self) -> bool:
        """Check if account is currently locked due to brute force protection."""
        if self.locked_until is None:
            return False
        return datetime.now(self.locked_until.tzinfo) < self.locked_until

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r} email={self.email!r}>"
