"""
PEVN — SA-01: SUPER_ADMIN Global Platform Governance, RBAC Enforcement, and Certification Suite

Automated regression verification for the SUPER_ADMIN role:
  TEST-01: Canonical Identity & Wildcard Claims (superadmin, level 100, institution_id None, *:*).
  TEST-02: Global Platform Administration Access (/health, /ready, /users, /institutions, /control-center).
  TEST-03: Institutional Context Requirement (Context-free -> 403 PERMISSION_DENIED; With Context -> 200).
  TEST-04: SuperAdmin Sensitive Access Technical Audit Logging (incidents, evaluations, etc.).
  TEST-05: Strict Role Separation: SUPER_ADMIN (level 100, *:*) vs NATIONAL_ADMIN (level 90, 30 canonical).
  TEST-06: Authentication & Inactive / Locked Account Rejection (401 Unauthorized).
  TEST-07: Anti-IDOR Tenant Boundary Verification.
"""

from collections.abc import AsyncGenerator
import uuid
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.audit.interfaces import AuditEventType
from app.audit.service import audit_service
from app.core.security.interfaces import OrganizationalScope, Permission, SystemRole
from app.core.security.tokens import token_service
from app.core.security.authorization import CentralizedAuthorizationService
from app.db.session import get_async_session
from app.main import create_application
from app.models.institution import Institution
from app.models.role import Role, UserRole
from app.models.user import User

PG_DB_URL = "postgresql+asyncpg://pevn_app:pevn_app_dev_pass@localhost:5433/pevn_db"


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated session connected to operational PostgreSQL."""
    engine = create_async_engine(PG_DB_URL, poolclass=NullPool)
    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an async test client connected to the application."""
    test_app = create_application()
    engine = create_async_engine(PG_DB_URL, poolclass=NullPool)
    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )

    async def _override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    test_app.dependency_overrides[get_async_session] = _override_get_async_session

    async with AsyncClient(
        transport=ASGITransport(app=test_app),  # type: ignore[arg-type]
        base_url="http://localhost",
        headers={"Host": "localhost"},
    ) as test_client:
        yield test_client

    await engine.dispose()


@pytest.fixture(scope="function")
async def superadmin_actor(db_session: AsyncSession) -> dict[str, Any]:
    """Resolve canonical SuperAdmin root user and auth headers."""
    stmt = (
        select(User)
        .join(UserRole, User.id == UserRole.user_id)
        .join(Role, UserRole.role_id == Role.id)
        .where(Role.name == "superadmin", User.is_active == True)
        .limit(1)
    )
    user = (await db_session.execute(stmt)).scalar_one_or_none()
    assert user is not None, "SuperAdmin user required in database."

    token = await token_service.create_access_token(subject=str(user.id))
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    return {"user": user, "token": token, "headers": headers}


@pytest.fixture(scope="function")
async def national_admin_actor(db_session: AsyncSession) -> dict[str, Any]:
    """Resolve canonical National Admin user and auth headers."""
    stmt = (
        select(User)
        .join(UserRole, User.id == UserRole.user_id)
        .join(Role, UserRole.role_id == Role.id)
        .where(Role.name == "national_admin", User.is_active == True)
        .limit(1)
    )
    user = (await db_session.execute(stmt)).scalar_one_or_none()
    assert user is not None, "National Admin user required in database."

    token = await token_service.create_access_token(subject=str(user.id))
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    return {"user": user, "token": token, "headers": headers}


@pytest.fixture(scope="function")
async def operational_institution(db_session: AsyncSession) -> Institution:
    """Resolve a valid operational institution for context testing."""
    stmt = select(Institution).where(Institution.is_active == True).limit(1)
    inst = (await db_session.execute(stmt)).scalar_one_or_none()
    assert inst is not None, "At least one operational institution required."
    return inst


# ===========================================================================
# TEST-01: Canonical Identity & Wildcard Claims
# ===========================================================================
@pytest.mark.asyncio
async def test_01_superadmin_canonical_identity_and_claims(
    client: AsyncClient,
    superadmin_actor: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    """
    Verify SUPER_ADMIN has canonical role 'superadmin', level 100,
    institution_id None, and wildcard access.
    """
    user: User = superadmin_actor["user"]
    headers: dict[str, str] = superadmin_actor["headers"]

    # 1. Check profile via API
    resp = await client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200, f"Expected 200 from /auth/me, got {resp.status_code}: {resp.text}"
    profile = resp.json()

    assert "superadmin" in profile["roles"], "Role 'superadmin' must be present in user roles."
    assert profile["institution_id"] is None, "SuperAdmin must have null institution_id by default."
    assert profile["scope"]["is_national"] is True, "SuperAdmin must have national/global administrative scope."

    # 2. Check Role definition in DB
    role_stmt = select(Role).where(Role.name == "superadmin")
    role = (await db_session.execute(role_stmt)).scalar_one()
    assert role.level == 100, f"SuperAdmin level must be 100, got {role.level}"
    assert len(role.permissions) >= 1, "SuperAdmin must possess wildcard permission."
    assert any(p.resource == "*" and p.action == "*" for p in role.permissions), (
        "SuperAdmin must have '*:*' permission assigned."
    )


# ===========================================================================
# TEST-02: Global Platform Administration Access
# ===========================================================================
@pytest.mark.asyncio
async def test_02_superadmin_global_administrative_endpoints(
    client: AsyncClient,
    superadmin_actor: dict[str, Any],
) -> None:
    """
    Verify SUPER_ADMIN can query global administration modules:
    - /health and /ready (System Diagnostics & Platform Health)
    - /users (Global Users Directory)
    - /institutions (National Institutions Catalog)
    - /analytics/territorial/control-center (Territorial Control Center)
    - /departments (Canonical Departments Catalog)
    """
    headers = superadmin_actor["headers"]

    # 1. Health & Readiness probes
    health_resp = await client.get("/api/v1/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "ok"

    ready_resp = await client.get("/api/v1/ready")
    assert ready_resp.status_code in {200, 503}  # 200 if dependencies ready

    # 2. Global Users Directory
    users_resp = await client.get("/api/v1/users", headers=headers)
    assert users_resp.status_code == 200, f"SuperAdmin should access users directory: {users_resp.text}"
    users_data = users_resp.json()
    assert "items" in users_data
    assert "total" in users_data
    assert users_data["total"] >= 1

    # 3. National Institutions Catalog
    inst_resp = await client.get("/api/v1/institutions", headers=headers)
    assert inst_resp.status_code == 200, f"SuperAdmin should access institutions: {inst_resp.text}"
    inst_data = inst_resp.json()
    assert "items" in inst_data
    assert "total" in inst_data

    # 4. Territorial Control Center
    cc_resp = await client.get("/api/v1/analytics/territorial/control-center", headers=headers)
    assert cc_resp.status_code == 200, f"SuperAdmin should access control-center: {cc_resp.text}"
    cc_data = cc_resp.json()
    assert "department_matrix" in cc_data
    assert len(cc_data["department_matrix"]) == 33

    # 5. Canonical Departments
    dept_resp = await client.get("/api/v1/departments", headers=headers)
    assert dept_resp.status_code == 200
    assert len(dept_resp.json()) == 33


# ===========================================================================
# TEST-03: Institutional Context Requirement
# ===========================================================================
@pytest.mark.asyncio
async def test_03_superadmin_institutional_context_requirement(
    client: AsyncClient,
    superadmin_actor: dict[str, Any],
    operational_institution: Institution,
) -> None:
    """
    Verify that SUPER_ADMIN:
    1. Without active institutional context: receives HTTP 403 PERMISSION_DENIED
       (Contexto institucional no disponible) on tenant-scoped modules.
    2. With active institutional context (X-Institution-Context header or institution_id query param):
       resolves the context and inspects resources within that tenant.
    """
    headers = superadmin_actor["headers"]
    inst_id = str(operational_institution.id)

    # --- Scenario A: Virtual Classrooms ---
    # Without context -> 403
    vc_no_ctx = await client.get("/api/v1/virtual-classrooms", headers=headers)
    assert vc_no_ctx.status_code == 403, (
        f"SuperAdmin without context must receive 403 on /virtual-classrooms, got {vc_no_ctx.status_code}"
    )
    assert "Contexto institucional no disponible" in vc_no_ctx.text

    # With X-Institution-Context header -> 200
    headers_with_ctx = {**headers, "X-Institution-Context": inst_id}
    vc_with_ctx = await client.get("/api/v1/virtual-classrooms", headers=headers_with_ctx)
    assert vc_with_ctx.status_code == 200, (
        f"SuperAdmin with X-Institution-Context must receive 200, got {vc_with_ctx.status_code}: {vc_with_ctx.text}"
    )
    assert "items" in vc_with_ctx.json()

    # With institution_id query param -> 200
    vc_with_query = await client.get(
        f"/api/v1/virtual-classrooms?institution_id={inst_id}",
        headers=headers,
    )
    assert vc_with_query.status_code == 200, (
        f"SuperAdmin with ?institution_id query param must receive 200, got {vc_with_query.status_code}"
    )

    # --- Scenario B: Academic Years ---
    # Without context -> 403
    ay_no_ctx = await client.get("/api/v1/academic-years", headers=headers)
    assert ay_no_ctx.status_code == 403, (
        f"SuperAdmin without context must receive 403 on /academic-years, got {ay_no_ctx.status_code}"
    )
    assert "Contexto institucional no disponible" in ay_no_ctx.text

    # With header -> 200
    ay_with_ctx = await client.get("/api/v1/academic-years", headers=headers_with_ctx)
    assert ay_with_ctx.status_code == 200, (
        f"SuperAdmin with X-Institution-Context must receive 200 on /academic-years, got {ay_with_ctx.status_code}"
    )


# ===========================================================================
# TEST-04: SuperAdmin Sensitive Access Technical Audit Logging
# ===========================================================================
@pytest.mark.asyncio
async def test_04_superadmin_sensitive_access_technical_audit(
    superadmin_actor: dict[str, Any],
    operational_institution: Institution,
    db_session: AsyncSession,
) -> None:
    """
    Verify that when SUPER_ADMIN accesses sensitive educational resources
    (incidents, evaluations, report_cards), CentralizedAuthorizationService
    records an explicit AuditEvent with SUSPICIOUS_ACTIVITY_DETECTED and
    metadata indicating 'superadmin_technical_access'.
    """
    from app.core.security.interfaces import AuthorizationContext

    user: User = superadmin_actor["user"]
    auth_service = CentralizedAuthorizationService()

    # Build auth context for superadmin
    context = AuthorizationContext(
        user_id=user.id,
        roles={SystemRole.SUPERADMIN},
        permissions={Permission(resource="*", action="*")},
        scope=OrganizationalScope(
            institution_id=str(operational_institution.id),
        ),
    )

    target_scope = OrganizationalScope(institution_id=str(operational_institution.id))

    # Check authorization for sensitive educational resource and verify audit event recording
    import unittest.mock
    sensitive_perm = Permission(resource="incidents", action="read")

    with unittest.mock.patch.object(
        audit_service, "record", new_callable=unittest.mock.AsyncMock
    ) as mock_record:
        is_authorized = await auth_service.authorize(context, sensitive_perm, target_scope)
        assert is_authorized is True, "SuperAdmin must be authorized via technical authority."

        mock_record.assert_awaited_once()
        recorded_event = mock_record.call_args[0][0]
        assert recorded_event.event_type == AuditEventType.SUSPICIOUS_ACTIVITY_DETECTED
        assert recorded_event.actor_id == user.id
        assert recorded_event.target_type == "incidents"
        assert "superadmin_technical_access" in str(recorded_event.metadata.get("action"))


# ===========================================================================
# TEST-05: Strict Role Separation: SUPER_ADMIN vs NATIONAL_ADMIN
# ===========================================================================
@pytest.mark.asyncio
async def test_05_strict_separation_superadmin_and_national_admin(
    client: AsyncClient,
    superadmin_actor: dict[str, Any],
    national_admin_actor: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    """
    Verify that:
    1. SUPER_ADMIN is level 100 with *:* wildcard.
    2. NATIONAL_ADMIN is level 90 and does NOT have *:* wildcard.
    3. NATIONAL_ADMIN cannot escalate to superadmin.
    4. NATIONAL_ADMIN permissions are confined to national governance and
       do not have school operational mutation permissions.
    """
    # 1. DB Levels
    sa_role = (await db_session.execute(select(Role).where(Role.name == "superadmin"))).scalar_one()
    na_role = (await db_session.execute(select(Role).where(Role.name == "national_admin"))).scalar_one()

    assert sa_role.level == 100, "SuperAdmin level must be 100."
    assert na_role.level == 90, "National Admin level must be 90."
    assert sa_role.level > na_role.level, "SuperAdmin hierarchy must strictly exceed National Admin."

    # 2. Wildcard check
    na_perms = {(p.resource, p.action) for p in na_role.permissions}
    assert ("*", "*") not in na_perms, "National Admin must NEVER possess '*:*' wildcard."

    # 3. Forbidden operational mutations for National Admin
    forbidden_mutations = [
        ("grades", "write"),
        ("groups", "create"),
        ("teachers", "create"),
        ("students", "create"),
        ("incidents", "close"),
    ]
    for res, act in forbidden_mutations:
        assert (res, act) not in na_perms, (
            f"National Admin must not possess operational school mutation ({res}:{act})."
        )


# ===========================================================================
# TEST-06: Authentication & Inactive / Locked Account Rejection
# ===========================================================================
@pytest.mark.asyncio
async def test_06_unauthenticated_and_inactive_accounts_rejected(
    client: AsyncClient,
    superadmin_actor: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    """
    Verify that:
    1. Unauthenticated requests to /api/v1/users are rejected with HTTP 401.
    2. Disabled/inactive accounts cannot execute privileged operations.
    """
    # 1. Unauthenticated request
    unauth_resp = await client.get("/api/v1/users")
    assert unauth_resp.status_code == 401, (
        f"Unauthenticated request must return 401, got {unauth_resp.status_code}"
    )

    # 2. Inactive account token test
    # Create an inactive user token
    fake_inactive_id = uuid.uuid4()
    inactive_user = User(
        id=fake_inactive_id,
        email=f"inactive_sa_{fake_inactive_id.hex[:6]}@pevn.edu.co",
        username=f"inactive_sa_{fake_inactive_id.hex[:6]}",
        hashed_password="some_hashed_password",
        first_name="Inactive",
        last_name="SuperAdmin",
        document_type="CC",
        document_number=f"INACT-{fake_inactive_id.hex[:6]}",
        is_active=False,  # Inactive account
    )
    db_session.add(inactive_user)
    await db_session.flush()

    sa_role = (await db_session.execute(select(Role).where(Role.name == "superadmin"))).scalar_one()
    user_role = UserRole(
        user_id=inactive_user.id,
        role_id=sa_role.id,
        is_active=True,
    )
    db_session.add(user_role)
    await db_session.commit()

    try:
        inactive_token = await token_service.create_access_token(subject=str(inactive_user.id))
        inactive_headers = {"Authorization": f"Bearer {inactive_token}"}

        resp = await client.get("/api/v1/users", headers=inactive_headers)
        assert resp.status_code == 401, (
            f"Inactive account must receive 401, got {resp.status_code}: {resp.text}"
        )
        assert "inactiva" in resp.text.lower(), "Response must indicate inactive account."
    finally:
        # Cleanup test user
        await db_session.delete(user_role)
        await db_session.delete(inactive_user)
        await db_session.commit()


# ===========================================================================
# TEST-07: Anti-IDOR Tenant Boundary Verification
# ===========================================================================
@pytest.mark.asyncio
async def test_07_anti_idor_tenant_boundary_verification(
    client: AsyncClient,
    operational_institution: Institution,
    db_session: AsyncSession,
) -> None:
    """
    Verify that an actor scoped to a specific institution (e.g. Rector)
    cannot supply an arbitrary institution_id parameter to access another tenant's users.
    """
    # 1. Resolve an institutional Rector
    stmt = (
        select(User)
        .join(UserRole, User.id == UserRole.user_id)
        .join(Role, UserRole.role_id == Role.id)
        .where(
            Role.name == "rector",
            User.is_active == True,
            User.institution_id != None,
        )
        .limit(1)
    )
    rector = (await db_session.execute(stmt)).scalar_one_or_none()
    if rector is None:
        pytest.skip("No Rector with active institution available for Anti-IDOR test.")

    rector_token = await token_service.create_access_token(subject=str(rector.id))
    rector_headers = {"Authorization": f"Bearer {rector_token}"}

    # Attempt to query users with a different institution_id
    foreign_inst_id = operational_institution.id
    if foreign_inst_id == rector.institution_id:
        # Find another institution
        stmt2 = select(Institution).where(Institution.id != rector.institution_id).limit(1)
        other_inst = (await db_session.execute(stmt2)).scalar_one_or_none()
        if other_inst is None:
            pytest.skip("No second institution available for IDOR test.")
        foreign_inst_id = other_inst.id

    # The rector's list_users endpoint will silently enforce the rector's actual institution_id
    # or reject unauthorized cross-tenant queries.
    resp = await client.get(
        f"/api/v1/users?institution_id={foreign_inst_id}",
        headers=rector_headers,
    )
    # The endpoint enforces current_user.institution_id for Rector
    if resp.status_code == 200:
        data = resp.json()
        for item in data.get("items", []):
            if item.get("institution_id"):
                assert str(item["institution_id"]) == str(rector.institution_id), (
                    f"Rector must only see users from own institution {rector.institution_id}, got {item['institution_id']}"
                )
