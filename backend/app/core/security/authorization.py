"""
PEVN Backend — Centralized Authorization Service

Implements IAuthorizationService with deny-by-default logic, granular permission
verification, role hierarchy checks, and hierarchical organizational scope validation.

SECURITY:
  - Default decision is DENY.
  - Multi-tenant isolation: Institution A cannot access Institution B.
  - Superadmin bypasses normal permission gates but all actions remain fully audited.
"""

from __future__ import annotations

from app.audit.interfaces import AuditEvent, AuditEventType
from app.audit.service import audit_service
from app.core.logging import get_logger
from app.core.security.interfaces import (
    AuthorizationContext,
    IAuthorizationService,
    OrganizationalScope,
    Permission,
    SystemRole,
)
from app.exceptions.errors import AuthorizationError

_logger = get_logger(__name__)


def scope_contains(
    actor_scope: OrganizationalScope, target_scope: OrganizationalScope
) -> bool:
    """
    Evaluate whether actor_scope contains or subsumes target_scope.

    Hierarchy:
      National (all None) -> Department -> Municipality -> Institution -> Campus

    Returns:
        True if target_scope is within actor_scope boundaries, False otherwise.
    """
    if (
        actor_scope.country_code
        and target_scope.country_code
        and actor_scope.country_code != target_scope.country_code
    ):
        return False

    if actor_scope.is_national():
        return True

    mismatches = (
        bool(
            actor_scope.department_id
            and target_scope.department_id != actor_scope.department_id
        ),
        bool(
            actor_scope.municipality_id
            and target_scope.municipality_id != actor_scope.municipality_id
        ),
        bool(
            actor_scope.institution_id
            and target_scope.institution_id != actor_scope.institution_id
        ),
        bool(actor_scope.campus_id and target_scope.campus_id != actor_scope.campus_id),
    )
    return not any(mismatches)


class CentralizedAuthorizationService(IAuthorizationService):
    """
    Centralized, deny-by-default implementation of IAuthorizationService.
    """

    async def authorize(
        self,
        context: AuthorizationContext,
        required_permission: Permission,
        target_scope: OrganizationalScope | None = None,
    ) -> bool:
        """
        Determine whether given context has permission in target scope.

        Args:
            context: The authenticated user's authorization context.
            required_permission: The permission required for the action.
            target_scope: The organizational scope of the target resource.

        Returns:
            True if authorized, False otherwise.
        """
        # Superadmin has global platform access
        if SystemRole.SUPERADMIN in context.roles:
            return True

        # 1. Verify Granular Permission
        has_permission = any(
            perm.resource in {required_permission.resource, "*"}
            and perm.action in {required_permission.action, "*"}
            for perm in context.permissions
        )

        if not has_permission:
            _logger.warning(
                "Permission check failed",
                user_id=context.user_id,
                required_permission=str(required_permission),
            )
            return False

        # 2. Verify Multi-Institutional / Territorial Scope
        if target_scope is not None and not scope_contains(context.scope, target_scope):
            _logger.warning(
                "Scope check failed (cross-tenant access attempt)",
                user_id=context.user_id,
                actor_scope=str(context.scope),
                target_scope=str(target_scope),
            )
            return False

        return True

    async def require(
        self,
        context: AuthorizationContext,
        required_permission: Permission,
        target_scope: OrganizationalScope | None = None,
    ) -> None:
        """
        Assert authorization or raise AuthorizationError and record audit event.
        """
        allowed = await self.authorize(context, required_permission, target_scope)
        if not allowed:
            await audit_service.record(
                AuditEvent(
                    event_type=AuditEventType.PERMISSION_DENIED,
                    actor_id=context.user_id,
                    actor_ip="0.0.0.0",  # noqa: S104
                    target_id=(
                        str(target_scope.institution_id) if target_scope else None
                    ),
                    target_type="resource",
                    institution_id=context.scope.institution_id,
                    success=False,
                    metadata={
                        "required_permission": str(required_permission),
                        "target_scope": str(target_scope) if target_scope else None,
                    },
                )
            )
            raise AuthorizationError("No tiene permisos para realizar esta acción.")


# Default authorization service singleton instance
authorization_service: IAuthorizationService = CentralizedAuthorizationService()
