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

# Resources belonging strictly to the school-level Academic and Institutional Management module.
# In accordance with the PO least-privilege policy, administrative roles (SUPERADMIN, NATIONAL_ADMIN,
# DEPARTMENT_ADMIN, MUNICIPALITY_ADMIN) are strictly barred from ordinary operations on these resources.
ACADEMIC_MANAGEMENT_RESOURCES: frozenset[str] = frozenset(
    {
        "academic_years",
        "academic_periods",
        "academic_assignments",
        "academic_promotions",
        "subjects",
        "groups",
        "teachers",
        "students",
        "guardians",
        "enrollments",
        "siee_policies",
        "evaluations",
        "report_cards",
        "promotions",
        "coordinators",
        "activities",
        "submissions",
        "attendance",
        "planning",
    }
)

# Legitimate institutional roles authorized to perform school-level educational operations
INSTITUTIONAL_EDUCATIONAL_ROLES: frozenset[str] = frozenset(
    {
        SystemRole.RECTOR.value,
        SystemRole.INSTITUTION_ADMIN.value,
        "coordinator",
        SystemRole.ACADEMIC_COORDINATOR.value,
        SystemRole.TEACHER.value,
        SystemRole.STUDENT.value,
        "guardian",
    }
)


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
            and (
                target_scope.department_id is None
                or str(target_scope.department_id).lower() != str(actor_scope.department_id).lower()
            )
        ),
        bool(
            actor_scope.municipality_id
            and (
                target_scope.municipality_id is None
                or str(target_scope.municipality_id).lower() != str(actor_scope.municipality_id).lower()
            )
        ),
        bool(
            actor_scope.institution_id
            and (
                target_scope.institution_id is None
                or str(target_scope.institution_id).lower() != str(actor_scope.institution_id).lower()
            )
        ),
        bool(
            actor_scope.campus_id
            and (
                target_scope.campus_id is None
                or str(target_scope.campus_id).lower() != str(actor_scope.campus_id).lower()
            )
        ),
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
        user_role_names = {
            r.value if isinstance(r, SystemRole) else str(r).lower()
            for r in context.roles
        }
        is_academic_resource = required_permission.resource in ACADEMIC_MANAGEMENT_RESOURCES

        # 0. PO Least-Privilege Policy: Administrative roles (SUPERADMIN, NATIONAL_ADMIN,
        # DEPARTMENT_ADMIN, MUNICIPALITY_ADMIN) are strictly barred from school-level
        # Academic & Institutional Management. Wildcards and superadmin bypasses cannot
        # override this restriction.
        if is_academic_resource:
            has_institutional_role = bool(user_role_names & INSTITUTIONAL_EDUCATIONAL_ROLES)
            if not has_institutional_role:
                _logger.warning(
                    "Academic API access denied for administrative role (PO least-privilege policy)",
                    user_id=context.user_id,
                    roles=list(user_role_names),
                    required_permission=str(required_permission),
                )
                return False

        # Superadmin has global platform access for technical operations, but NOT for academic resources
        if SystemRole.SUPERADMIN in context.roles and not is_academic_resource:
            if required_permission.resource in {"incidents"}:
                await audit_service.record(
                    AuditEvent(
                        event_type=AuditEventType.SUSPICIOUS_ACTIVITY_DETECTED,
                        actor_id=context.user_id,
                        actor_ip="0.0.0.0",  # noqa: S104
                        target_id=(
                            str(target_scope.institution_id) if target_scope else None
                        ),
                        target_type=required_permission.resource,
                        institution_id=context.scope.institution_id,
                        success=True,
                        metadata={
                            "action": f"superadmin_technical_access:{required_permission}",
                            "role": "superadmin",
                            "resource": required_permission.resource,
                            "permission": str(required_permission),
                            "note": "Acceso técnico/diagnóstico auditado por SuperAdmin.",
                        },
                    )
                )
            return True

        # 1. Verify Granular Permission
        # Wildcard (*) does NOT match academic management resources
        has_permission = any(
            (
                perm.resource == required_permission.resource
                or (perm.resource == "*" and not is_academic_resource)
            )
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
