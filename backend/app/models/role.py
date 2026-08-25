"""
PEVN Backend — RBAC & Permission Domain Models

Implements formal Role-Based Access Control with fine-grained permissions
and institutional/campus-scoped role assignments.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models.institution import Campus, Institution
    from app.models.user import User


class Role(Base):
    """
    System Role Definition.

    Maps to SystemRole taxonomy (superadmin, national_admin, department_admin,
    municipality_admin, rector, coordinator, teacher, student, guardian, auditor).
    """

    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Machine name of the role (e.g. 'rector', 'teacher').",
    )
    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Human readable role name (e.g. 'Rector / Director').",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Detailed description of role responsibilities.",
    )
    level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc=(
            "Hierarchy level (100 = superadmin, 10 = student) to "
            "prevent vertical escalation."
        ),
    )

    # Relationships
    permissions: Mapped[list[Permission]] = relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles",
        lazy="selectin",
    )
    user_roles: Mapped[list[UserRole]] = relationship(
        "UserRole",
        back_populates="role",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Role name={self.name!r} level={self.level}>"


class Permission(Base):
    """
    Granular Permission.

    Represents an atomic action on a resource (e.g. 'users:create', 'grades:read').
    """

    __tablename__ = "permissions"
    __table_args__ = (
        UniqueConstraint("resource", "action", name="uq_permissions_resource_action"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    resource: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Resource name (e.g. 'users', 'institutions', 'audit_logs').",
    )
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Action name (e.g. 'read', 'create', 'update', 'delete', 'export').",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Description of what this permission grants.",
    )

    # Relationships
    roles: Mapped[list[Role]] = relationship(
        "Role",
        secondary="role_permissions",
        back_populates="permissions",
        lazy="selectin",
    )

    @property
    def identifier(self) -> str:
        """Return resource:action string (e.g. 'users:read')."""
        return f"{self.resource}:{self.action}"

    def __repr__(self) -> str:
        return f"<Permission {self.identifier}>"


class RolePermission(Base):
    """
    Role to Permission association table.
    """

    __tablename__ = "role_permissions"

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    )


class UserRole(Base):
    """
    User to Role Assignment with optional Institutional and Campus Scoping.
    """

    __tablename__ = "user_roles"

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
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    institution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Institution scope for this role assignment (NULL for national roles).",
    )
    campus_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campuses.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Campus scope for this role assignment (NULL for institution-wide roles).",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Whether this role assignment is currently active.",
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped[User] = relationship(
        "User",
        back_populates="user_roles",
        lazy="selectin",
    )
    role: Mapped[Role] = relationship(
        "Role",
        back_populates="user_roles",
        lazy="selectin",
    )
    institution: Mapped[Institution | None] = relationship(
        "Institution",
        back_populates="user_roles",
        lazy="selectin",
    )
    campus: Mapped[Campus | None] = relationship(
        "Campus",
        back_populates="user_roles",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<UserRole user_id={self.user_id} role_id={self.role_id}>"
