"""
PEVN Backend — Token Domain Models

Implements secure storage for Refresh Tokens (with rotation family tracking
and reuse detection) and Password Reset Tokens (single use, SHA-256 hashed).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.user import User


class RefreshToken(Base):
    """
    Refresh Token Record.

    Only the SHA-256 hash of the token is stored.
    Belongs to a token family (family_id) to enable replay attack detection.
    """

    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User who owns this token.",
    )
    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        doc="SHA-256 hex digest of the raw refresh token.",
    )
    family_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        doc="Token family UUID for rotation and reuse detection.",
    )
    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether this individual token has been revoked.",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="UTC expiration timestamp for this refresh token.",
    )
    created_ip: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        doc="Client IP address where the token was issued.",
    )
    user_agent: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Client User-Agent header string.",
    )
    replaced_by_token_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("refresh_tokens.id", ondelete="SET NULL"),
        nullable=True,
        doc="Reference to the new token issued during rotation.",
    )

    # Relationships
    user: Mapped[User] = relationship(
        "User",
        back_populates="refresh_tokens",
        lazy="selectin",
    )

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now(self.expires_at.tzinfo) >= self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if token is active, unrevoked, unreplaced, and unexpired."""
        return (
            not self.is_revoked
            and self.replaced_by_token_id is None
            and not self.is_expired
        )

    def __repr__(self) -> str:
        return (
            f"<RefreshToken id={self.id} user_id={self.user_id} "
            f"revoked={self.is_revoked}>"
        )


class PasswordResetToken(Base):
    """
    Password Reset Token Record.

    Only the SHA-256 hash is stored. Single-use, short expiration (1 hour).
    """

    __tablename__ = "password_reset_tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="User who requested the password reset.",
    )
    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        doc="SHA-256 hex digest of the raw password reset token.",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="UTC expiration timestamp for this reset token.",
    )
    is_used: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether this token has already been consumed.",
    )

    # Relationships
    user: Mapped[User] = relationship(
        "User",
        back_populates="password_reset_tokens",
        lazy="selectin",
    )

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now(self.expires_at.tzinfo) >= self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if token is unused and unexpired."""
        return not self.is_used and not self.is_expired

    def __repr__(self) -> str:
        return (
            f"<PasswordResetToken id={self.id} user_id={self.user_id} "
            f"used={self.is_used}>"
        )
