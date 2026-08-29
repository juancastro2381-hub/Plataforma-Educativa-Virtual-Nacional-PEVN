"""
PEVN Backend — Territorial Analytics Endpoints & Multi-Tenant Isolation Tests

Tests hierarchical territorial aggregations, department/municipality distributions,
institutional KPI retrieval, and strict cross-tenant/cross-scope isolation barriers.
"""

from __future__ import annotations

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.models.institution import Campus, Institution
from app.models.official_catalog import (
    OfficialCampusCatalog,
    OfficialInstitutionCatalog,
)
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User


async def _setup_territorial_fixtures(
    db: AsyncSession,
) -> dict[str, str | uuid.UUID]:
    """Helper to set up departments, municipalities, official catalogs, institutions, and users."""
    # 1. Departments
    dept_bog = Department(code="11", name="Bogotá D.C.")
    dept_ant = Department(code="05", name="Antioquia")
    db.add_all([dept_bog, dept_ant])
    await db.flush()

    # 2. Municipalities
    mun_bog = Municipality(department_id=dept_bog.id, code="11001", name="Bogotá D.C.")
    mun_med = Municipality(department_id=dept_ant.id, code="05001", name="Medellín")
    db.add_all([mun_bog, mun_med])
    await db.flush()

    # 3. Official Institution Catalog
    cat_inst_1 = OfficialInstitutionCatalog(
        dane_code="111001000100",
        name="Institución Educativa Distrital República de Colombia",
        department_code="11",
        department_name="Bogotá D.C.",
        municipality_code="11001",
        municipality_name="Bogotá D.C.",
        sector="OFICIAL",
        zone="URBANA",
        calendar="A",
        academic_character="ACADÉMICO",
        is_active=True,
    )
    cat_inst_2 = OfficialInstitutionCatalog(
        dane_code="105001000200",
        name="Colegio Mayor de Antioquia",
        department_code="05",
        department_name="Antioquia",
        municipality_code="05001",
        municipality_name="Medellín",
        sector="OFICIAL",
        zone="URBANA",
        calendar="A",
        academic_character="ACADÉMICO",
        is_active=True,
    )
    db.add_all([cat_inst_1, cat_inst_2])
    await db.flush()

    # 4. Official Campuses Catalog
    cat_camp_1 = OfficialCampusCatalog(
        official_institution_id=cat_inst_1.id,
        dane_sede_code="111001000100-01",
        name="Sede Principal",
        is_main=True,
        zone="URBANA",
        is_active=True,
    )
    cat_camp_2 = OfficialCampusCatalog(
        official_institution_id=cat_inst_2.id,
        dane_sede_code="105001000200-01",
        name="Sede Central",
        is_main=True,
        zone="URBANA",
        is_active=True,
    )
    db.add_all([cat_camp_1, cat_camp_2])
    await db.flush()

    # 5. Provisioned Institution in PEvN
    inst_a = Institution(
        municipality_id=mun_bog.id,
        dane_code="111001000100",
        name="Institución Educativa Distrital República de Colombia",
        email="rectoria@iedcolombia.edu.co",
        is_active=True,
    )
    inst_b = Institution(
        municipality_id=mun_med.id,
        dane_code="105001000200",
        name="Colegio Mayor de Antioquia",
        email="rectoria@colmayor.edu.co",
        is_active=True,
    )
    db.add_all([inst_a, inst_b])
    await db.flush()

    camp_a = Campus(
        institution_id=inst_a.id,
        dane_sede_code="111001000100-01",
        name="Sede Principal A",
        is_active=True,
    )
    camp_b = Campus(
        institution_id=inst_b.id,
        dane_sede_code="105001000200-01",
        name="Sede Principal B",
        is_active=True,
    )
    db.add_all([camp_a, camp_b])
    await db.flush()

    # 6. Roles
    nat_admin_role_res = await db.execute(
        select(Role).where(Role.name == SystemRole.NATIONAL_ADMIN.value)
    )
    nat_admin_role = nat_admin_role_res.scalar_one()

    rector_role_res = await db.execute(
        select(Role).where(Role.name == SystemRole.RECTOR.value)
    )
    rector_role = rector_role_res.scalar_one()

    # 7. Users
    nat_admin_user = User(
        email="nat_admin@mineducacion.gov.co",
        username="natadmin",
        hashed_password=password_hasher.hash("NatAdminSecure123!"),
        first_name="Admin",
        last_name="Nacional",
        document_type=DocumentType.CC,
        document_number="9988776655",
        institution_id=None,
        is_active=True,
        is_verified=True,
        must_change_password=False,
    )
    rector_a = User(
        email="rector_a@iedcolombia.edu.co",
        username="rector_a",
        hashed_password=password_hasher.hash("RectorSecure123!"),
        first_name="Rector",
        last_name="Bogota",
        document_type=DocumentType.CC,
        document_number="8877665544",
        institution_id=inst_a.id,
        is_active=True,
        is_verified=True,
        must_change_password=False,
    )
    db.add_all([nat_admin_user, rector_a])
    await db.flush()

    db.add_all([
        UserRole(user_id=nat_admin_user.id, role_id=nat_admin_role.id, institution_id=None, is_active=True),
        UserRole(user_id=rector_a.id, role_id=rector_role.id, institution_id=inst_a.id, is_active=True),
    ])
    await db.commit()

    return {
        "inst_a_id": str(inst_a.id),
        "inst_b_id": str(inst_b.id),
    }


@pytest.mark.asyncio
async def test_territorial_summary_national_scope(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Test GET /api/v1/analytics/territorial/summary with national scope."""
    await _setup_territorial_fixtures(db_session)

    # Login as National Admin
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": "natadmin", "password": "NatAdminSecure123!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/analytics/territorial/summary", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["scope_level"] == "NATIONAL"
    assert data["jurisdiction_name"] == "República de Colombia"
    assert data["total_departments"] >= 2
    assert data["total_municipalities"] >= 2
    assert data["total_institutions"] >= 2
    assert data["provisioned_institutions"] >= 2
    assert data["provisioning_rate_percent"] > 0
    assert data["total_campuses"] >= 2
    assert "sector_breakdown" in data
    assert "zone_breakdown" in data


@pytest.mark.asyncio
async def test_territorial_department_distribution_national_scope(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Test GET /api/v1/analytics/territorial/departments with national scope."""
    await _setup_territorial_fixtures(db_session)

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": "natadmin", "password": "NatAdminSecure123!"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/analytics/territorial/departments", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_count"] >= 2
    dept_codes = [d["department_code"] for d in data["items"]]
    assert "11" in dept_codes
    assert "05" in dept_codes


@pytest.mark.asyncio
async def test_territorial_municipality_distribution(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Test GET /api/v1/analytics/territorial/municipalities with department filter."""
    await _setup_territorial_fixtures(db_session)

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": "natadmin", "password": "NatAdminSecure123!"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get(
        "/api/v1/analytics/territorial/municipalities?department_code=11",
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["department_code"] == "11"
    assert data["total_count"] >= 1
    assert data["items"][0]["municipality_code"] == "11001"


@pytest.mark.asyncio
async def test_institutional_kpis_and_cross_tenant_isolation(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """
    CRITICAL MULTI-TENANT TEST:
    Rector from Institution A can read KPIs for Institution A,
    but MUST BE BLOCKED (403 Forbidden) when attempting to access Institution B.
    """
    fixtures = await _setup_territorial_fixtures(db_session)
    inst_a_id = fixtures["inst_a_id"]
    inst_b_id = fixtures["inst_b_id"]

    # Login as Rector A
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": "rector_a", "password": "RectorSecure123!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Rector A accessing own institution KPIs -> 200 OK
    own_res = await client.get(
        f"/api/v1/analytics/territorial/institutions/{inst_a_id}",
        headers=headers,
    )
    assert own_res.status_code == 200
    assert own_res.json()["institution_id"] == inst_a_id
    assert own_res.json()["total_campuses"] == 1

    # 2. Rector A accessing foreign institution B KPIs -> 403 Forbidden!
    foreign_res = await client.get(
        f"/api/v1/analytics/territorial/institutions/{inst_b_id}",
        headers=headers,
    )
    assert foreign_res.status_code == 403
    assert foreign_res.json()["error"]["code"] == "PERMISSION_DENIED"

    # 3. Rector A attempting to access national department breakdown -> 403 Forbidden!
    dept_res = await client.get(
        "/api/v1/analytics/territorial/departments",
        headers=headers,
    )
    assert dept_res.status_code == 403
    assert dept_res.json()["error"]["code"] == "PERMISSION_DENIED"
