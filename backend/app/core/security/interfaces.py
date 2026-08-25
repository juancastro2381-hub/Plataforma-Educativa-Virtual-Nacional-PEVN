"""
PEVN Backend — Security Abstractions and Interfaces

Defines the core security contracts for authentication, authorization,
password hashing, and token management.

PHASE 1 STATUS:
  These are interface definitions only. Concrete implementations will be
  added in Phase 2 (Authentication & Authorization).

  DO NOT implement workaround authentication here.
  DO NOT use these interfaces as stubs that silently allow all access.

Design Principles:
  - Role-Based Access Control (RBAC) combined with explicit Permissions
  - Organizational Scope (institution-level data isolation is mandatory)
  - Resource ownership is part of authorization decisions
  - Business rules can further restrict access
  - All authorization decisions must be explicit, not implicit

The final authorization model:
  ALLOW IF:
    user has required Role
    AND user has required Permission
    AND user's Scope includes the target Resource
    AND Business Rules do not deny access
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

# ---------------------------------------------------------------------------
# Permission and Scope domain types
# ---------------------------------------------------------------------------


class SystemRole(StrEnum):
    """
    Top-level system roles.

    Phase 1: Defines the role taxonomy for future implementation.
    The final system will use these roles as part of a combined
    RBAC + permission + scope authorization model.

    Hierarchy (highest privilege first):
      SUPERADMIN > NATIONAL_ADMIN > DEPARTMENT_ADMIN > MUNICIPALITY_ADMIN
      > INSTITUTION_ADMIN > RECTOR > ACADEMIC_COORDINATOR > TEACHER > STUDENT
    """

    # Platform administration (government / operator level)
    SUPERADMIN = "superadmin"
    NATIONAL_ADMIN = "national_admin"
    DEPARTMENT_ADMIN = "department_admin"
    MUNICIPALITY_ADMIN = "municipality_admin"

    # Institution administration
    INSTITUTION_ADMIN = "institution_admin"
    RECTOR = "rector"
    ACADEMIC_COORDINATOR = "academic_coordinator"

    # Educational actors
    TEACHER = "teacher"
    STUDENT = "student"

    # Support roles
    SUPPORT = "support"
    OBSERVER = "observer"


@dataclass(frozen=True)
class Permission:
    """
    A granular permission that gates access to a specific action.

    Permissions are independent of roles. The authorization system
    checks both the user's role AND their explicit permissions.

    Examples:
      Permission(resource="grades", action="write")
      Permission(resource="attendance", action="read")
      Permission(resource="recordings", action="download")
    """

    resource: str
    action: str

    def __str__(self) -> str:
        return f"{self.resource}:{self.action}"


@dataclass(frozen=True)
class OrganizationalScope:
    """
    Defines the organizational boundary within which a user can operate.

    Institutional isolation is enforced by scopes:
    - A user with institution_id=A cannot access data for institution_id=B
      unless they have a scope that explicitly includes B (e.g., national admin)
    - Scope narrows from national → department → municipality → institution → campus

    Phase 1: Data class defined for future authorization implementation.
    """

    # Territorial hierarchy (None = access to all at that level)
    country_code: str | None = "CO"
    department_id: str | None = None
    municipality_id: str | None = None
    institution_id: str | None = None
    campus_id: str | None = None

    def is_national(self) -> bool:
        """True if the scope covers all institutions in the country."""
        return (
            self.department_id is None
            and self.municipality_id is None
            and self.institution_id is None
        )

    def is_department(self) -> bool:
        """True if the scope is limited to a specific department."""
        return self.department_id is not None and self.municipality_id is None

    def is_institution(self) -> bool:
        """True if the scope is limited to a specific institution."""
        return self.institution_id is not None


@dataclass
class AuthorizationContext:
    """
    Full context provided to authorization checks.

    Encapsulates everything needed to make an authorization decision
    without requiring the authorizer to reach into the HTTP request.
    """

    user_id: str
    roles: list[SystemRole]
    permissions: list[Permission]
    scope: OrganizationalScope
    # Additional context available to business rule evaluators
    extra: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Interface definitions
# ---------------------------------------------------------------------------


class IPasswordHasher(ABC):
    """
    Contract for password hashing implementations.

    Phase 2 will implement this using Argon2id (preferred) or bcrypt.
    NEVER use MD5, SHA-1, SHA-256, or any non-purpose-built algorithm
    for password storage.
    """

    @abstractmethod
    def hash(self, password: str) -> str:
        """
        Hash a plaintext password.

        Args:
            password: The plaintext password to hash.

        Returns:
            The hashed password string (includes algorithm, salt, parameters).

        SECURITY: The password parameter must never be logged.
        """
        raise NotImplementedError

    @abstractmethod
    def verify(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plaintext password against its stored hash.

        Args:
            plain_password: The password to verify.
            hashed_password: The stored hash to verify against.

        Returns:
            True if the password matches, False otherwise.

        SECURITY: This must be timing-safe (constant-time comparison).
        """
        raise NotImplementedError

    @abstractmethod
    def needs_rehash(self, hashed_password: str) -> bool:
        """
        Check whether the hash needs to be upgraded.

        Returns True if the hashing parameters have changed and
        the password should be rehashed on next successful login.
        """
        raise NotImplementedError


class ITokenService(ABC):
    """
    Contract for token generation and validation.

    Phase 2 will implement JWT-based access + refresh tokens.
    The token strategy must support:
      - Short-lived access tokens (minutes)
      - Longer-lived refresh tokens (hours/days)
      - Token revocation (via Redis blocklist or similar mechanism)
    """

    @abstractmethod
    async def create_access_token(
        self,
        subject: str,
        additional_claims: dict[str, Any] | None = None,
    ) -> str:
        """
        Create a signed access token.

        Args:
            subject: The token subject (typically user ID).
            additional_claims: Optional extra claims to embed in the token.

        Returns:
            A signed token string.

        SECURITY: Never embed sensitive data (passwords, full PII) in tokens.
        """
        raise NotImplementedError

    @abstractmethod
    async def verify_token(self, token: str) -> dict[str, Any]:
        """
        Verify and decode a token.

        Args:
            token: The token string to verify.

        Returns:
            The decoded payload if the token is valid.

        Raises:
            SecurityException: If the token is invalid, expired, or revoked.
        """
        raise NotImplementedError

    @abstractmethod
    async def revoke_token(self, token: str) -> None:
        """
        Revoke a token so it cannot be used again.
        Implementations should use Redis or similar for the revocation store.
        """
        raise NotImplementedError


class IAuthenticationService(ABC):
    """
    Contract for user authentication.

    Phase 2 will implement credential-based authentication.
    The service is responsible for verifying identity only —
    NOT for determining what the authenticated user can do.
    """

    @abstractmethod
    async def authenticate(
        self,
        username: str,
        password: str,
    ) -> AuthorizationContext | None:
        """
        Authenticate a user by credentials.

        Args:
            username: The user's username or email.
            password: The plaintext password to verify.

        Returns:
            AuthorizationContext if authentication succeeds, None otherwise.

        SECURITY:
          - Passwords must never be logged.
          - Failed attempts must be audited.
          - Implement account lockout to prevent brute force attacks.
        """
        raise NotImplementedError


class IAuthorizationService(ABC):
    """
    Contract for authorization decisions.

    The authorization model is:
      Role + Permission + OrganizationalScope + Business Rules → decision

    This MUST be the single, centralized place where authorization
    decisions are made. Business logic and route handlers must
    delegate to this service, never implement their own checks.
    """

    @abstractmethod
    async def authorize(
        self,
        context: AuthorizationContext,
        required_permission: Permission,
        target_scope: OrganizationalScope | None = None,
    ) -> bool:
        """
        Determine whether the given context has the required permission.

        Args:
            context: The authenticated user's authorization context.
            required_permission: The permission required for the action.
            target_scope: The scope of the resource being accessed.
                          If None, uses the context's own scope.

        Returns:
            True if the action is authorized, False otherwise.

        SECURITY:
          - Default to DENY. Only explicitly grant access.
          - Institutional isolation: a context scoped to institution A
            must never access resources belonging to institution B.
        """
        raise NotImplementedError

    @abstractmethod
    async def require(
        self,
        context: AuthorizationContext,
        required_permission: Permission,
        target_scope: OrganizationalScope | None = None,
    ) -> None:
        """
        Assert authorization or raise an exception.

        Equivalent to calling authorize() and raising a PermissionDenied
        exception if the result is False.

        Raises:
            PermissionDenied: If authorization fails.
        """
        raise NotImplementedError
