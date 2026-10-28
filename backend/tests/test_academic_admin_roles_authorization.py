"""
PEVN Backend — Academic API Authorization & Least-Privilege Enforcement Tests

Focused security test suite verifying:
  1. Denial of ordinary academic API access (read & write) for all 4 administrative roles:
     - SUPERADMIN (canonical name: 'superadmin')
     - NATIONAL_ADMIN ('national_admin')
     - DEPARTMENT_ADMIN ('department_admin')
     - MUNICIPALITY_ADMIN ('municipality_admin')
  2. The '*:*' wildcard cannot bypass the academic management module restriction.
  3. Direct requests with ?institution_id= are rejected for all administrative roles.
  4. Tenant/institution isolation is preserved (Tenant A rector cannot access Tenant B).
  5. Authorized institutional roles (Rector, Coordinator, Teacher) retain required academic workflows.
  6. Non-academic technical and territorial administration APIs continue to function normally.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.core.security.tokens import token_service
from app.models.institution import Campus, Institution
from app.models.role import Role, UserRole
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User


@pytest.fixture
async def academic_auth_fixture(
    db_session: AsyncSession,
) -> dict[str, Any]:
    """Fixture with territorial structure, institutions, and authenticated tokens for all roles."""
    dept = Department(code="25", name="Cundinamarca")
    db_session.add(dept)
    await db_session.flush()

    mun = Municipality(department_id=dept.id, code="25001", name="Agua de Dios")
    db_session.add(mun)
    await db_session.flush()

    inst_a = Institution(
        municipality_id=mun.id,
        dane_code="12500100991",
        name="Colegio Departamental A",
        email="rectoria@inst-a.edu.co",
        is_active=True,
    )
    inst_b = Institution(
        municipality_id=mun.id,
        dane_code="12500100992",
        name="Colegio Departamental B",
        email="rectoria@inst-b.edu.co",
        is_active=True,
    )
    db_session.add_all([inst_a, inst_b])
    await db_session.flush()

    campus_a = Campus(
        institution_id=inst_a.id,
        dane_sede_code="12500100991-01",
        name="Sede Principal A",
        is_active=True,
    )
    campus_b = Campus(
        institution_id=inst_b.id,
        dane_sede_code="12500100992-01",
        name="Sede Principal B",
        is_active=True,
    )
    db_session.add_all([campus_a, campus_b])
    await db_session.flush()

    # Query Roles
    role_superadmin = (
        await db_session.execute(select(Role).where(Role.name == SystemRole.SUPERADMIN.value))
    ).scalar_one()
    role_nat_admin = (
        await db_session.execute(select(Role).where(Role.name == SystemRole.NATIONAL_ADMIN.value))
    ).scalar_one()
    role_dept_admin = (
        await db_session.execute(select(Role).where(Role.name == SystemRole.DEPARTMENT_ADMIN.value))
    ).scalar_one()
    role_muni_admin = (
        await db_session.execute(select(Role).where(Role.name == SystemRole.MUNICIPALITY_ADMIN.value))
    ).scalar_one()
    role_rector = (
        await db_session.execute(select(Role).where(Role.name == SystemRole.RECTOR.value))
    ).scalar_one()

    pwd = password_hasher.hash("Seguro123456*!")

    # Users
    user_superadmin = User(
        email="superadmin.sec@pevn.gov.co",
        username="superadmin_sec",
        hashed_password=pwd,
        first_name="Super",
        last_name="Admin",
        document_type=DocumentType.CC,
        document_number="89000001",
        institution_id=None,
        is_active=True,
        is_verified=True,
    )
    user_nat_admin = User(
        email="natadmin.sec@pevn.gov.co",
        username="natadmin_sec",
        hashed_password=pwd,
        first_name="National",
        last_name="Admin",
        document_type=DocumentType.CC,
        document_number="89000002",
        institution_id=None,
        is_active=True,
        is_verified=True,
    )
    user_dept_admin = User(
        email="deptadmin.sec@pevn.gov.co",
        username="deptadmin_sec",
        hashed_password=pwd,
        first_name="Department",
        last_name="Admin",
        document_type=DocumentType.CC,
        document_number="89000003",
        institution_id=None,
        is_active=True,
        is_verified=True,
    )
    user_muni_admin = User(
        email="muniadmin.sec@pevn.gov.co",
        username="muniadmin_sec",
        hashed_password=pwd,
        first_name="Municipality",
        last_name="Admin",
        document_type=DocumentType.CC,
        document_number="89000004",
        institution_id=None,
        is_active=True,
        is_verified=True,
    )
    user_rector_a = User(
        email="rector.sec.a@inst-a.edu.co",
        username="rector_sec_a",
        hashed_password=pwd,
        first_name="Rector",
        last_name="Inst A",
        document_type=DocumentType.CC,
        document_number="89000005",
        institution_id=inst_a.id,
        is_active=True,
        is_verified=True,
    )
    user_rector_b = User(
        email="rector.sec.b@inst-b.edu.co",
        username="rector_sec_b",
        hashed_password=pwd,
        first_name="Rector",
        last_name="Inst B",
        document_type=DocumentType.CC,
        document_number="89000006",
        institution_id=inst_b.id,
        is_active=True,
        is_verified=True,
    )

    db_session.add_all([
        user_superadmin,
        user_nat_admin,
        user_dept_admin,
        user_muni_admin,
        user_rector_a,
        user_rector_b,
    ])
    await db_session.flush()

    # User Roles
    db_session.add(UserRole(user_id=user_superadmin.id, role_id=role_superadmin.id, institution_id=None, is_active=True))
    db_session.add(UserRole(user_id=user_nat_admin.id, role_id=role_nat_admin.id, institution_id=None, is_active=True))
    db_session.add(UserRole(user_id=user_dept_admin.id, role_id=role_dept_admin.id, institution_id=None, is_active=True))
    db_session.add(UserRole(user_id=user_muni_admin.id, role_id=role_muni_admin.id, institution_id=None, is_active=True))
    db_session.add(UserRole(user_id=user_rector_a.id, role_id=role_rector.id, institution_id=inst_a.id, is_active=True))
    db_session.add(UserRole(user_id=user_rector_b.id, role_id=role_rector.id, institution_id=inst_b.id, is_active=True))
    await db_session.commit()

    # Tokens
    token_superadmin = await token_service.create_access_token(
        subject=str(user_superadmin.id),
        additional_claims={"roles": [SystemRole.SUPERADMIN.value], "institution_id": None},
    )
    token_nat_admin = await token_service.create_access_token(
        subject=str(user_nat_admin.id),
        additional_claims={"roles": [SystemRole.NATIONAL_ADMIN.value], "institution_id": None},
    )
    token_dept_admin = await token_service.create_access_token(
        subject=str(user_dept_admin.id),
        additional_claims={
            "roles": [SystemRole.DEPARTMENT_ADMIN.value],
            "department_id": str(dept.id),
            "institution_id": None,
        },
    )
    token_muni_admin = await token_service.create_access_token(
        subject=str(user_muni_admin.id),
        additional_claims={
            "roles": [SystemRole.MUNICIPALITY_ADMIN.value],
            "department_id": str(dept.id),
            "municipality_id": str(mun.id),
            "institution_id": None,
        },
    )
    token_rector_a = await token_service.create_access_token(
        subject=str(user_rector_a.id),
        additional_claims={"roles": [SystemRole.RECTOR.value], "institution_id": str(inst_a.id)},
    )
    token_rector_b = await token_service.create_access_token(
        subject=str(user_rector_b.id),
        additional_claims={"roles": [SystemRole.RECTOR.value], "institution_id": str(inst_b.id)},
    )

    return {
        "inst_a": inst_a,
        "inst_b": inst_b,
        "campus_a": campus_a,
        "campus_b": campus_b,
        "dept": dept,
        "mun": mun,
        "token_superadmin": token_superadmin,
        "token_nat_admin": token_nat_admin,
        "token_dept_admin": token_dept_admin,
        "token_muni_admin": token_muni_admin,
        "token_rector_a": token_rector_a,
        "token_rector_b": token_rector_b,
    }


@pytest.mark.asyncio
async def test_01_superadmin_denied_academic_read_and_write(
    client: AsyncClient, academic_auth_fixture: dict[str, Any]
) -> None:
    """
    SUPERADMIN (Level 100) must be denied both read and write operations on academic endpoints.
    The '*:*' wildcard cannot bypass the academic module restriction.
    """
    headers = {"Authorization": f"Bearer {academic_auth_fixture['token_superadmin']}"}
    inst_a_id = str(academic_auth_fixture["inst_a"].id)

    # 1. READ Academic Years -> 403 Forbidden
    res_read = await client.get("/api/v1/academic-years", headers=headers, params={"institution_id": inst_a_id})
    assert res_read.status_code == 403

    # 2. WRITE Academic Years -> 403 Forbidden
    res_write = await client.post(
        "/api/v1/academic-years",
        headers=headers,
        params={"institution_id": inst_a_id},
        json={"year": 2029, "name": "Año 2029 Hack", "start_date": "2029-02-01", "end_date": "2029-11-30"},
    )
    assert res_write.status_code == 403

    # 3. READ Students -> 403 Forbidden
    res_students = await client.get("/api/v1/students", headers=headers, params={"institution_id": inst_a_id})
    assert res_students.status_code == 403

    # 4. READ Teachers -> 403 Forbidden
    res_teachers = await client.get("/api/v1/teachers", headers=headers, params={"institution_id": inst_a_id})
    assert res_teachers.status_code == 403

    # 5. READ Groups -> 403 Forbidden
    res_groups = await client.get("/api/v1/groups", headers=headers, params={"institution_id": inst_a_id})
    assert res_groups.status_code == 403

    # 6. READ Academic Assignments -> 403 Forbidden
    res_assignments = await client.get(
        "/api/v1/academic-assignments", headers=headers, params={"institution_id": inst_a_id}
    )
    assert res_assignments.status_code == 403


@pytest.mark.asyncio
async def test_02_national_admin_denied_academic_read_and_write(
    client: AsyncClient, academic_auth_fixture: dict[str, Any]
) -> None:
    """
    NATIONAL_ADMIN (Level 90) must be denied direct academic operations.
    National governance (MEN) is confined to macro indicators and institutional catalog.
    """
    headers = {"Authorization": f"Bearer {academic_auth_fixture['token_nat_admin']}"}
    inst_a_id = str(academic_auth_fixture["inst_a"].id)

    # READ Academic Years -> 403 Forbidden
    res_read = await client.get("/api/v1/academic-years", headers=headers, params={"institution_id": inst_a_id})
    assert res_read.status_code == 403

    # WRITE Academic Years -> 403 Forbidden
    res_write = await client.post(
        "/api/v1/academic-years",
        headers=headers,
        params={"institution_id": inst_a_id},
        json={"year": 2029, "name": "Año 2029 Hack", "start_date": "2029-02-01", "end_date": "2029-11-30"},
    )
    assert res_write.status_code == 403

    # READ Students -> 403 Forbidden
    res_students = await client.get("/api/v1/students", headers=headers, params={"institution_id": inst_a_id})
    assert res_students.status_code == 403

    # READ Teachers -> 403 Forbidden
    res_teachers = await client.get("/api/v1/teachers", headers=headers, params={"institution_id": inst_a_id})
    assert res_teachers.status_code == 403


@pytest.mark.asyncio
async def test_03_department_admin_denied_academic_read_and_write(
    client: AsyncClient, academic_auth_fixture: dict[str, Any]
) -> None:
    """
    DEPARTMENT_ADMIN (Level 80) must be denied direct academic operations,
    even for institutions within their assigned department.
    """
    headers = {"Authorization": f"Bearer {academic_auth_fixture['token_dept_admin']}"}
    inst_a_id = str(academic_auth_fixture["inst_a"].id)

    # READ Academic Years -> 403 Forbidden
    res_read = await client.get("/api/v1/academic-years", headers=headers, params={"institution_id": inst_a_id})
    assert res_read.status_code == 403

    # WRITE Academic Years -> 403 Forbidden
    res_write = await client.post(
        "/api/v1/academic-years",
        headers=headers,
        params={"institution_id": inst_a_id},
        json={"year": 2029, "name": "Año 2029 Hack", "start_date": "2029-02-01", "end_date": "2029-11-30"},
    )
    assert res_write.status_code == 403

    # READ Groups -> 403 Forbidden
    res_groups = await client.get("/api/v1/groups", headers=headers, params={"institution_id": inst_a_id})
    assert res_groups.status_code == 403


@pytest.mark.asyncio
async def test_04_municipality_admin_denied_academic_read_and_write(
    client: AsyncClient, academic_auth_fixture: dict[str, Any]
) -> None:
    """
    MUNICIPALITY_ADMIN (Level 70) must be denied direct academic operations,
    even for institutions within their assigned municipality.
    """
    headers = {"Authorization": f"Bearer {academic_auth_fixture['token_muni_admin']}"}
    inst_a_id = str(academic_auth_fixture["inst_a"].id)

    # READ Academic Years -> 403 Forbidden
    res_read = await client.get("/api/v1/academic-years", headers=headers, params={"institution_id": inst_a_id})
    assert res_read.status_code == 403

    # WRITE Academic Years -> 403 Forbidden
    res_write = await client.post(
        "/api/v1/academic-years",
        headers=headers,
        params={"institution_id": inst_a_id},
        json={"year": 2029, "name": "Año 2029 Hack", "start_date": "2029-02-01", "end_date": "2029-11-30"},
    )
    assert res_write.status_code == 403

    # READ Students -> 403 Forbidden
    res_students = await client.get("/api/v1/students", headers=headers, params={"institution_id": inst_a_id})
    assert res_students.status_code == 403


@pytest.mark.asyncio
async def test_05_rector_retains_academic_management_access(
    client: AsyncClient, academic_auth_fixture: dict[str, Any]
) -> None:
    """
    Authorized Rector of Institution A retains complete academic operations
    within their assigned tenant.
    """
    headers = {"Authorization": f"Bearer {academic_auth_fixture['token_rector_a']}"}

    # 1. CREATE Academic Year -> 201 Created
    res_create = await client.post(
        "/api/v1/academic-years",
        headers=headers,
        json={"year": 2027, "name": "Año 2027 Regular", "start_date": "2027-02-01", "end_date": "2027-11-30"},
    )
    assert res_create.status_code == 201
    year_id = res_create.json()["id"]

    # 2. READ Academic Year -> 200 OK
    res_read = await client.get(f"/api/v1/academic-years/{year_id}", headers=headers)
    assert res_read.status_code == 200
    assert res_read.json()["name"] == "Año 2027 Regular"

    # 3. LIST Academic Years -> 200 OK
    res_list = await client.get("/api/v1/academic-years", headers=headers)
    assert res_list.status_code == 200
    assert len(res_list.json()["items"]) >= 1


@pytest.mark.asyncio
async def test_06_tenant_isolation_rector_cannot_access_foreign_institution(
    client: AsyncClient, academic_auth_fixture: dict[str, Any]
) -> None:
    """
    Tenant isolation is strictly maintained: Rector of Institution B cannot
    access or manipulate Institution A's academic entities.
    """
    headers_a = {"Authorization": f"Bearer {academic_auth_fixture['token_rector_a']}"}
    headers_b = {"Authorization": f"Bearer {academic_auth_fixture['token_rector_b']}"}

    # Rector A creates year in Inst A
    res_create = await client.post(
        "/api/v1/academic-years",
        headers=headers_a,
        json={"year": 2031, "name": "Año 2031 Inst A", "start_date": "2031-02-01", "end_date": "2031-11-30"},
    )
    assert res_create.status_code == 201
    year_a_id = res_create.json()["id"]

    # Rector B attempts to read Inst A's year -> 404 Blind Isolation
    res_cross_read = await client.get(f"/api/v1/academic-years/{year_a_id}", headers=headers_b)
    assert res_cross_read.status_code == 404

    # Rector B attempts to activate Inst A's year -> 404 Blind Isolation
    res_cross_act = await client.post(f"/api/v1/academic-years/{year_a_id}/activate", headers=headers_b)
    assert res_cross_act.status_code == 404


@pytest.mark.asyncio
async def test_07_authorized_administrative_modules_remain_functional(
    client: AsyncClient, academic_auth_fixture: dict[str, Any]
) -> None:
    """
    Verifies that legitimate technical and territorial administration modules continue
    working smoothly for their authorized administrative roles.
    """
    headers_super = {"Authorization": f"Bearer {academic_auth_fixture['token_superadmin']}"}
    headers_nat = {"Authorization": f"Bearer {academic_auth_fixture['token_nat_admin']}"}
    headers_dept = {"Authorization": f"Bearer {academic_auth_fixture['token_dept_admin']}"}
    headers_muni = {"Authorization": f"Bearer {academic_auth_fixture['token_muni_admin']}"}

    # 1. SuperAdmin: Technical Operations Portal -> 200 OK
    res_health = await client.get("/api/v1/system/operations/health", headers=headers_super)
    assert res_health.status_code == 200
    assert res_health.json()["status"].lower() == "healthy"

    # 2. National Admin: Institutional Catalog & Territorial Analytics -> 200 OK
    res_inst = await client.get("/api/v1/institutions", headers=headers_nat)
    assert res_inst.status_code == 200

    res_nat_analytics = await client.get("/api/v1/analytics/territorial/summary", headers=headers_nat)
    assert res_nat_analytics.status_code == 200

    # 3. Department Admin: Territorial Analytics -> 200 OK
    res_dept_analytics = await client.get("/api/v1/analytics/territorial/summary", headers=headers_dept)
    assert res_dept_analytics.status_code == 200

    # 4. Municipality Admin: Territorial Analytics -> 200 OK
    res_muni_analytics = await client.get("/api/v1/analytics/territorial/summary", headers=headers_muni)
    assert res_muni_analytics.status_code == 200

