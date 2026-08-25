"""
PEVN Backend — Authentication and Multi-Tenant Endpoints Integration Tests

Tests HTTP endpoint behaviors, HttpOnly cookie lifecycle, Bearer authorization headers,
profile inspection, and cross-tenant institution access barriers.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.models.institution import Campus, Institution
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User


async def _setup_institution_and_users(
    db: AsyncSession,
) -> dict[str, User | Institution]:
    """Helper to set up departments, municipalities, institutions, and users."""
    dept = Department(
        code="11",
        name="Bogotá D.C.",
    )
    db.add(dept)
    await db.flush()

    mun = Municipality(
        department_id=dept.id,
        code="11001",
        name="Bogotá D.C.",
    )
    db.add(mun)
    await db.flush()

    # Institution A
    inst_a = Institution(
        municipality_id=mun.id,
        dane_code="11100100001",
        name="Colegio Distrital Nacional A",
        email="contacto@colegioa.edu.co",
        is_active=True,
    )
    db.add(inst_a)

    # Institution B
    inst_b = Institution(
        municipality_id=mun.id,
        dane_code="11100100002",
        name="Colegio Distrital Nacional B",
        email="contacto@colegiob.edu.co",
        is_active=True,
    )
    db.add(inst_b)
    await db.flush()

    # Add campuses
    campus_a = Campus(
        institution_id=inst_a.id,
        dane_sede_code="11100100001-01",
        name="Sede Principal A",
        is_active=True,
    )
    db.add(campus_a)
    await db.flush()

    # Roles
    teacher_role_res = await db.execute(
        select(Role).where(Role.name == SystemRole.TEACHER.value)
    )
    teacher_role = teacher_role_res.scalar_one()

    inst_read_perm_res = await db.execute(
        select(Permission).where(
            Permission.resource == "institutions",
            Permission.action == "read",
        )
    )
    inst_read_perm = inst_read_perm_res.scalar_one()

    # Assign institutions:read permission to teacher role
    role_perm = RolePermission(
        role_id=teacher_role.id,
        permission_id=inst_read_perm.id,
    )
    db.add(role_perm)
    await db.flush()

    # User in Institution A
    user_a = User(
        email="teacher_a@pevn.edu.co",
        username="teacher_a",
        hashed_password=password_hasher.hash("SecurePasswordA123!"),
        first_name="Profesor",
        last_name="Colegio A",
        document_type=DocumentType.CC,
        document_number="1000000001",
        institution_id=inst_a.id,
        is_active=True,
        is_verified=True,
        must_change_password=False,
    )
    db.add(user_a)
    await db.flush()

    user_a_role = UserRole(
        user_id=user_a.id,
        role_id=teacher_role.id,
        institution_id=inst_a.id,
        is_active=True,
    )
    db.add(user_a_role)

    await db.commit()
    await db.refresh(user_a)
    await db.refresh(inst_a)
    await db.refresh(inst_b)

    return {
        "user_a": user_a,
        "inst_a": inst_a,
        "inst_b": inst_b,
    }


@pytest.mark.asyncio
async def test_login_endpoint_success_and_cookie(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Test POST /api/v1/auth/login sets HttpOnly cookie and returns valid access token."""
    await _setup_institution_and_users(db_session)

    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "teacher_a", "password": "SecurePasswordA123!"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 900
    assert data["user"]["username"] == "teacher_a"
    assert data["user"]["email"] == "teacher_a@pevn.edu.co"
    assert "teacher" in data["user"]["roles"]

    # Verify HttpOnly Cookie
    assert "pevn_refresh_token" in response.cookies
    refresh_cookie = response.cookies["pevn_refresh_token"]
    assert len(refresh_cookie) >= 48


@pytest.mark.asyncio
async def test_login_endpoint_invalid_password(client: AsyncClient) -> None:
    """Test POST /api/v1/auth/login with wrong credentials returns 401."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "non_existent_user", "password": "AnyPassword123!"},
    )
    assert response.status_code == 401
    assert "error" in response.json()
    assert response.json()["error"]["code"] == "AUTHENTICATION_FAILED"


@pytest.mark.asyncio
async def test_refresh_and_logout_endpoints(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Test POST /api/v1/auth/refresh and POST /api/v1/auth/logout with cookies."""
    await _setup_institution_and_users(db_session)

    # 1. Login
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": "teacher_a", "password": "SecurePasswordA123!"},
    )
    assert login_res.status_code == 200
    refresh_cookie = login_res.cookies.get("pevn_refresh_token")
    assert refresh_cookie is not None

    # 2. Refresh token using cookie
    refresh_res = await client.post(
        "/api/v1/auth/refresh",
        cookies={"pevn_refresh_token": refresh_cookie},
    )
    assert refresh_res.status_code == 200
    refresh_data = refresh_res.json()
    assert "access_token" in refresh_data
    new_refresh_cookie = refresh_res.cookies.get("pevn_refresh_token")
    assert new_refresh_cookie is not None
    assert new_refresh_cookie != refresh_cookie

    # 3. Logout
    logout_res = await client.post(
        "/api/v1/auth/logout",
        cookies={"pevn_refresh_token": new_refresh_cookie},
    )
    assert logout_res.status_code == 200
    assert logout_res.json()["message"] == "Sesión cerrada correctamente."


@pytest.mark.asyncio
async def test_get_my_profile_authenticated_and_unauthenticated(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Test GET /api/v1/auth/me returns 401 without Bearer token and 200 with Bearer token."""
    await _setup_institution_and_users(db_session)

    # Unauthenticated request
    unauth_res = await client.get("/api/v1/auth/me")
    assert unauth_res.status_code == 401

    # Login to obtain access token
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": "teacher_a", "password": "SecurePasswordA123!"},
    )
    access_token = login_res.json()["access_token"]

    # Authenticated request with Bearer header
    auth_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert auth_res.status_code == 200
    me_data = auth_res.json()
    assert me_data["username"] == "teacher_a"
    assert me_data["scope"]["institution_id"] is not None


@pytest.mark.asyncio
async def test_multi_tenant_institutional_isolation(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """
    CRITICAL MULTI-TENANT TEST:
    A user from Institution A can read Institution A,
    but MUST BE BLOCKED (403 Forbidden) when attempting to access Institution B.
    """
    fixtures = await _setup_institution_and_users(db_session)
    inst_a = fixtures["inst_a"]
    inst_b = fixtures["inst_b"]

    # Login as User from Institution A
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": "teacher_a", "password": "SecurePasswordA123!"},
    )
    access_token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # 1. Accessing /institutions/me returns Institution A
    me_inst_res = await client.get("/api/v1/institutions/me", headers=headers)
    assert me_inst_res.status_code == 200
    assert me_inst_res.json()["name"] == "Colegio Distrital Nacional A"
    assert len(me_inst_res.json()["campuses"]) == 1

    # 2. Accessing own institution by ID (/institutions/{inst_a.id}) returns 200
    own_inst_res = await client.get(
        f"/api/v1/institutions/{inst_a.id}",
        headers=headers,
    )
    assert own_inst_res.status_code == 200
    assert own_inst_res.json()["id"] == str(inst_a.id)

    # 3. Accessing foreign institution by ID (/institutions/{inst_b.id}) returns 403 FORBIDDEN!
    foreign_inst_res = await client.get(
        f"/api/v1/institutions/{inst_b.id}",
        headers=headers,
    )
    assert foreign_inst_res.status_code == 403
    assert "error" in foreign_inst_res.json()
    assert foreign_inst_res.json()["error"]["code"] == "PERMISSION_DENIED"
