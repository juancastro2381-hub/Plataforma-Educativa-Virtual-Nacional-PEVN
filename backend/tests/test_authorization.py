"""
PEVN Backend — Centralized Authorization Service Unit Tests

Tests deny-by-default logic, granular permissions, role hierarchies,
and multi-tenant hierarchical organizational scope barriers.
"""

from __future__ import annotations

import pytest

from app.core.security.authorization import authorization_service, scope_contains
from app.core.security.interfaces import (
    AuthorizationContext,
    OrganizationalScope,
    Permission,
    SystemRole,
)
from app.exceptions.errors import AuthorizationError


def test_scope_contains_hierarchy() -> None:
    """Test hierarchical scope containment checks."""
    national_scope = OrganizationalScope(
        country_code="CO",
        department_id=None,
        municipality_id=None,
        institution_id=None,
        campus_id=None,
    )
    dept_a_scope = OrganizationalScope(
        country_code="CO",
        department_id="dept-11",
        municipality_id=None,
        institution_id=None,
    )
    dept_b_scope = OrganizationalScope(
        country_code="CO",
        department_id="dept-25",
        municipality_id=None,
        institution_id=None,
    )
    inst_a1_scope = OrganizationalScope(
        country_code="CO",
        department_id="dept-11",
        municipality_id="mun-11001",
        institution_id="inst-aaa",
    )
    inst_a2_scope = OrganizationalScope(
        country_code="CO",
        department_id="dept-11",
        municipality_id="mun-11001",
        institution_id="inst-bbb",
    )

    # 1. National scope contains all sub-entities
    assert scope_contains(national_scope, dept_a_scope) is True
    assert scope_contains(national_scope, inst_a1_scope) is True

    # 2. Department A scope contains Institution A1 (which is in Dept A)
    assert scope_contains(dept_a_scope, inst_a1_scope) is True

    # 3. Department A does NOT contain Department B
    assert scope_contains(dept_a_scope, dept_b_scope) is False

    # 4. Multi-tenant barrier: Institution A1 cannot access Institution A2
    assert scope_contains(inst_a1_scope, inst_a2_scope) is False

    # 5. Same Institution scope contains itself
    assert scope_contains(inst_a1_scope, inst_a1_scope) is True


@pytest.mark.asyncio
async def test_superadmin_bypasses_all_checks() -> None:
    """Test that SuperAdmin is always authorized regardless of permission or target scope."""
    superadmin_context = AuthorizationContext(
        user_id="user-superadmin",
        roles=[SystemRole.SUPERADMIN],
        permissions=[],  # No explicit permissions needed
        scope=OrganizationalScope(country_code="CO"),
    )

    target_scope = OrganizationalScope(institution_id="inst-xyz")
    permission = Permission(resource="system_config", action="delete")

    assert (
        await authorization_service.authorize(
            context=superadmin_context,
            required_permission=permission,
            target_scope=target_scope,
        )
        is True
    )


@pytest.mark.asyncio
async def test_user_with_permission_and_matching_scope_authorized() -> None:
    """Test that a user with the required permission in their institution is authorized."""
    teacher_context = AuthorizationContext(
        user_id="user-teacher-1",
        roles=[SystemRole.TEACHER],
        permissions=[
            Permission(resource="grades", action="write"),
            Permission(resource="attendance", action="write"),
        ],
        scope=OrganizationalScope(institution_id="inst-colegio-1"),
    )

    # Authorized when operating within own institution
    assert (
        await authorization_service.authorize(
            context=teacher_context,
            required_permission=Permission(resource="grades", action="write"),
            target_scope=OrganizationalScope(institution_id="inst-colegio-1"),
        )
        is True
    )

    # Denied when attempting cross-tenant access to another institution
    assert (
        await authorization_service.authorize(
            context=teacher_context,
            required_permission=Permission(resource="grades", action="write"),
            target_scope=OrganizationalScope(institution_id="inst-colegio-2"),
        )
        is False
    )

    # Denied when lacking permission
    assert (
        await authorization_service.authorize(
            context=teacher_context,
            required_permission=Permission(resource="institutions", action="delete"),
            target_scope=OrganizationalScope(institution_id="inst-colegio-1"),
        )
        is False
    )


@pytest.mark.asyncio
async def test_wildcard_permission_matching() -> None:
    """Test that wildcard permissions (*:*) grant access."""
    admin_context = AuthorizationContext(
        user_id="user-admin-1",
        roles=[SystemRole.INSTITUTION_ADMIN],
        permissions=[
            Permission(resource="users", action="*"),
        ],
        scope=OrganizationalScope(institution_id="inst-colegio-1"),
    )

    assert (
        await authorization_service.authorize(
            context=admin_context,
            required_permission=Permission(resource="users", action="create"),
            target_scope=OrganizationalScope(institution_id="inst-colegio-1"),
        )
        is True
    )
    assert (
        await authorization_service.authorize(
            context=admin_context,
            required_permission=Permission(resource="users", action="delete"),
            target_scope=OrganizationalScope(institution_id="inst-colegio-1"),
        )
        is True
    )


@pytest.mark.asyncio
async def test_require_raises_authorization_error() -> None:
    """Test that require() raises AuthorizationError when unauthorized."""
    student_context = AuthorizationContext(
        user_id="user-student-1",
        roles=[SystemRole.STUDENT],
        permissions=[Permission(resource="grades", action="read")],
        scope=OrganizationalScope(institution_id="inst-colegio-1"),
    )

    with pytest.raises(AuthorizationError, match="No tiene permisos"):
        await authorization_service.require(
            context=student_context,
            required_permission=Permission(resource="grades", action="write"),
            target_scope=OrganizationalScope(institution_id="inst-colegio-1"),
        )
