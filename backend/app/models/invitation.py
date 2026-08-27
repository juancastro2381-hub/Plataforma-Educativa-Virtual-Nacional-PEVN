"""
PEVN Backend — Rector Invitation Domain Model

Represents cryptographically secure, single-use, time-limited onboarding
invitations issued by National Administrators to institutional Rectors.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.institution import Institution
    from app.models.user import User


class RectorInvitation(Base):
    """
    Rector Onboarding Invitation Record.

    Stores the SHA-256 hash of a cryptographically random 48-byte URL-safe token.
    Raw tokens are NEVER persisted to the database.
    """

    __tablename__ = "rector_invitations"

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
        doc="Target educational institution where the rector will be assigned.",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Pre-registered inactive User account for the rector.",
    )
    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        doc="SHA-256 hex digest of the raw 48-byte invitation token.",
    )
    invited_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="National Administrator or Superadmin who issued the invitation.",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="UTC timestamp when this invitation expires (default: 48h).",
    )
    is_used: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether this invitation token has already been redeemed.",
    )
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="UTC timestamp when the invitation was successfully redeemed.",
    )
    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether this invitation was manually revoked or superseded.",
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="UTC timestamp when the invitation was revoked.",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="UTC timestamp of creation.",
    )

    # Relationships
    institution: Mapped[Institution] = relationship(
        "Institution",
        lazy="selectin",
    )
    user: Mapped[User] = relationship(
        "User",
        foreign_keys=[user_id],
        lazy="selectin",
    )
    invited_by: Mapped[User] = relationship(
        "User",
        foreign_keys=[invited_by_id],
        lazy="selectin",
    )

    @property
    def is_expired(self) -> bool:
        """Check if invitation has passed its expiration time."""
        if self.expires_at.tzinfo is not None:
            now = datetime.now(self.expires_at.tzinfo)
        else:
            now = datetime.now(UTC).replace(tzinfo=None)
        return now >= self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if invitation is unused, unrevoked, and unexpired."""
        return not self.is_used and not self.is_revoked and not self.is_expired

    def __repr__(self) -> str:
        return (
            f"<RectorInvitation id={self.id} institution_id={self.institution_id} "
            f"user_id={self.user_id} used={self.is_used}>"
        )
