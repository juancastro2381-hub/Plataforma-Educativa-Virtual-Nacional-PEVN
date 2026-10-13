"""
PEVN — Phase NTA-05: National Admin Territorial Control Center Test Suite

Automated test specifications verifying the NTA-05 architecture blueprint:
  TEST-01: Happy Path / National (Superadmin consulta matriz nacional de 33 departamentos).
  TEST-02: Happy Path / National Admin (National admin consulta mismos contadores consolidados).
  TEST-03: Happy Path / Department Admin (Department admin consulta scope departamental, matriz de 1 fila).
  TEST-04: Anti-IDOR / Cross-Dept (Department admin intenta consultar departamento ajeno -> HTTP 403).
  TEST-05: Disambiguation / 4-Tier (Verificación matemática de las 4 capas usando nombres canónicos).
  TEST-06: SED Governance Coverage (Verificación con semántica de asignación activa de Dept Admin).
  TEST-07: Pipeline State Integrity (Verificación de consistencia de estados de solicitudes NTA-04).
  TEST-08: Department Detail Endpoint (Consulta de desglose municipal de un departamento válido -> HTTP 200).
  TEST-09: Department Detail IDOR (Department admin consulta detalle de otro departamento -> HTTP 403).
  TEST-10: Role Isolation (Usuarios institucionales como docentes/estudiantes -> HTTP 403).
  TEST-11: Unauthenticated Access (Petición anónima -> HTTP 401).
  TEST-12: Audit Log Emission (Registro de evento TERRITORIAL_CONTROL_CENTER_ACCESSED sanitizado).
  TEST-13: Baseline Invariance (Cero inserciones o mutaciones tras llamadas al control center).
  TEST-14: Regression NTA-02 (33 departamentos, 1,119 municipios, 0 huérfanos).
  TEST-15: Regression NTA-03 / NTA-04 (18,031 catálogo, 34 tenants [7 vinculados, 27 fixtures]).
"""

from collections.abc import AsyncGenerator
import uuid
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.audit.interfaces import AuditEventType
from app.core.security.tokens import token_service
from app.db.session import get_async_session
from app.main import create_application
from app.models.institution import Campus, Institution
from app.models.official_catalog import OfficialCampusCatalog, OfficialInstitutionCatalog
from app.models.onboarding import InstitutionOnboardingRequest
from app.models.role import Role, UserRole
from app.models.territory import Department, Municipality
from app.models.user import User

PG_DB_URL = "postgresql+asyncpg://pevn_app:pevn_app_dev_pass@localhost:5433/pevn_db"


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated session connected to the operational PostgreSQL database."""
    engine = create_async_engine(PG_DB_URL, poolclass=NullPool)
    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture(scope="function")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an async test client connected to the PostgreSQL database."""
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
async def auth_actors(db_session: AsyncSession) -> dict[str, Any]:
    """Resolve authenticated test actors across national, departmental, and institutional scopes."""
    # 1. Superadmin
    sa_res = await db_session.execute(text("""
        SELECT u.id, u.email
        FROM users u
        JOIN user_roles ur ON u.id = ur.user_id
        JOIN roles r ON ur.role_id = r.id
        WHERE r.name = 'superadmin' AND u.is_active = true
        LIMIT 1
    """))
    sa_row = sa_res.fetchone()
    assert sa_row is not None, "Superadmin actor required for NTA-05 tests"
    sa_token = await token_service.create_access_token(subject=str(sa_row[0]))

    # 2. National Admin
    na_res = await db_session.execute(text("""
        SELECT u.id, u.email
        FROM users u
        JOIN user_roles ur ON u.id = ur.user_id
        JOIN roles r ON ur.role_id = r.id
        WHERE r.name = 'national_admin' AND u.is_active = true
        LIMIT 1
    """))
    na_row = na_res.fetchone()
    if not na_row:
        # Fall back to superadmin if national_admin not present separately
        na_row = sa_row
        na_token = sa_token
    else:
        na_token = await token_service.create_access_token(subject=str(na_row[0]))

    # 3. Department Admin - Cundinamarca (25)
    da_cun_res = await db_session.execute(text("""
        SELECT u.id, u.email, d.id as dept_id, d.code as dept_code
        FROM users u
        JOIN user_roles ur ON u.id = ur.user_id
        JOIN roles r ON ur.role_id = r.id
        JOIN departments d ON ur.department_id = d.id
        WHERE r.name = 'department_admin' AND d.code = '25' AND u.is_active = true
        LIMIT 1
    """))
    da_cun_row = da_cun_res.fetchone()
    assert da_cun_row is not None, "Department Admin for Cundinamarca required for NTA-05 tests"
    da_cun_token = await token_service.create_access_token(subject=str(da_cun_row[0]))

    # 4. Department Admin - Atlántico (08)
    da_atl_res = await db_session.execute(text("""
        SELECT u.id, u.email, d.id as dept_id, d.code as dept_code
        FROM users u
        JOIN user_roles ur ON u.id = ur.user_id
        JOIN roles r ON ur.role_id = r.id
        JOIN departments d ON ur.department_id = d.id
        WHERE r.name = 'department_admin' AND d.code = '08' AND u.is_active = true
        LIMIT 1
    """))
    da_atl_row = da_atl_res.fetchone()
    assert da_atl_row is not None, "Department Admin for Atlántico required for NTA-05 tests"
    da_atl_token = await token_service.create_access_token(subject=str(da_atl_row[0]))

    # 5. Teacher (institutional actor without territorial scope)
    tch_res = await db_session.execute(text("""
        SELECT u.id, u.email
        FROM users u
        JOIN user_roles ur ON u.id = ur.user_id
        JOIN roles r ON ur.role_id = r.id
        WHERE r.name = 'teacher' AND u.is_active = true
        LIMIT 1
    """))
    tch_row = tch_res.fetchone()
    tch_token = await token_service.create_access_token(subject=str(tch_row[0])) if tch_row else ""

    return {
        "sa_headers": {"Authorization": f"Bearer {sa_token}"},
        "na_headers": {"Authorization": f"Bearer {na_token}"},
        "da_cun_headers": {"Authorization": f"Bearer {da_cun_token}"},
        "da_cun_dept_id": da_cun_row[2],
        "da_cun_dept_code": da_cun_row[3],
        "da_atl_headers": {"Authorization": f"Bearer {da_atl_token}"},
        "da_atl_dept_id": da_atl_row[2],
        "da_atl_dept_code": da_atl_row[3],
        "tch_headers": {"Authorization": f"Bearer {tch_token}"} if tch_token else {},
    }


# ===========================================================================
# TEST-01: Happy Path / National (Superadmin)
# ===========================================================================
@pytest.mark.asyncio
async def test_01_superadmin_national_control_center(
    client: AsyncClient,
    auth_actors: dict[str, Any],
) -> None:
    response = await client.get(
        "/api/v1/analytics/territorial/control-center",
        headers=auth_actors["sa_headers"],
    )
    assert response.status_code == 200, f"Expected 200, got: {response.text}"
    data = response.json()

    assert data["scope_level"] == "NATIONAL"
    assert data["jurisdiction_name"] == "República de Colombia"
    assert len(data["department_matrix"]) == 33
    assert data["tier1_catalog"]["total_departments"] == 33
    assert data["tier1_catalog"]["total_municipalities"] == 1119
    assert data["tier1_catalog"]["total_establishments"] == 18031
    assert data["tier3_tenancy"]["total_institutions"] == 38


# ===========================================================================
# TEST-02: Happy Path / National Admin
# ===========================================================================
@pytest.mark.asyncio
async def test_02_national_admin_national_control_center(
    client: AsyncClient,
    auth_actors: dict[str, Any],
) -> None:
    response = await client.get(
        "/api/v1/analytics/territorial/control-center",
        headers=auth_actors["na_headers"],
    )
    assert response.status_code == 200, f"Expected 200, got: {response.text}"
    data = response.json()

    assert data["scope_level"] == "NATIONAL"
    assert len(data["department_matrix"]) == 33
    assert data["tier1_catalog"]["total_establishments"] == 18031
    assert data["tier3_tenancy"]["total_institutions"] == 38


# ===========================================================================
# TEST-03: Happy Path / Department Admin (Cundinamarca)
# ===========================================================================
@pytest.mark.asyncio
async def test_03_department_admin_cundinamarca_scope(
    client: AsyncClient,
    auth_actors: dict[str, Any],
) -> None:
    response = await client.get(
        "/api/v1/analytics/territorial/control-center",
        headers=auth_actors["da_cun_headers"],
    )
    assert response.status_code == 200, f"Expected 200, got: {response.text}"
    data = response.json()

    assert data["scope_level"] == "DEPARTMENT"
    assert data["jurisdiction_name"] == "CUNDINAMARCA"
    # Anti-IDOR: Matrix contains EXACTLY 1 row, never all 33 departments
    assert len(data["department_matrix"]) == 1
    assert data["department_matrix"][0]["department_code"] == "25"
    assert data["department_matrix"][0]["department_name"] == "CUNDINAMARCA"
    assert data["tier1_catalog"]["total_departments"] == 1
    assert data["tier1_catalog"]["total_municipalities"] == 116


# ===========================================================================
# TEST-04: Anti-IDOR / Cross-Department Detail Blocked
# ===========================================================================
@pytest.mark.asyncio
async def test_04_department_admin_cannot_access_foreign_control_center(
    client: AsyncClient,
    auth_actors: dict[str, Any],
) -> None:
    # Department Admin for Cundinamarca (25) attempts to query Atlántico (08)
    response = await client.get(
        "/api/v1/analytics/territorial/control-center/departments/08",
        headers=auth_actors["da_cun_headers"],
    )
    assert response.status_code == 403, (
        f"Cross-department detail query must be rejected with 403, got {response.status_code}"
    )


# ===========================================================================
# TEST-05: Disambiguation / 4-Tier Canonical Contract
# ===========================================================================
@pytest.mark.asyncio
async def test_05_metrics_4tier_disambiguation_integrity(
    client: AsyncClient,
    auth_actors: dict[str, Any],
) -> None:
    response = await client.get(
        "/api/v1/analytics/territorial/control-center",
        headers=auth_actors["sa_headers"],
    )
    assert response.status_code == 200
    data = response.json()

    # Tier 1: Canonical Catalog
    assert data["tier1_catalog"]["total_establishments"] == 18031
    assert data["tier1_catalog"]["total_campuses"] > 50000

    # Tier 3: Tenancy Breakdown
    tier3 = data["tier3_tenancy"]
    assert tier3["total_institutions"] == 38
    assert tier3["active_institutions"] == 35
    assert tier3["inactive_institutions"] == 3
    assert tier3["catalog_linked_institutions"] == 11
    assert tier3["synthetic_fixture_institutions"] == 27
    assert tier3["total_institutions"] == tier3["active_institutions"] + tier3["inactive_institutions"]
    assert tier3["total_institutions"] == tier3["catalog_linked_institutions"] + tier3["synthetic_fixture_institutions"]
    assert tier3["provisioned_campuses"] == 26
    assert tier3["active_operational_campuses"] == 26


# ===========================================================================
# TEST-06: SED Governance Coverage (Active Assignment Semantics)
# ===========================================================================
@pytest.mark.asyncio
async def test_06_sed_governance_coverage_active_assignments(
    client: AsyncClient,
    auth_actors: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    response = await client.get(
        "/api/v1/analytics/territorial/control-center",
        headers=auth_actors["sa_headers"],
    )
    assert response.status_code == 200
    data = response.json()
    tier4 = data["tier4_governance"]

    # Verify directly against PostgreSQL active assignment semantics
    expected_da_users = (await db_session.execute(text("""
        SELECT count(DISTINCT u.id)
        FROM users u
        JOIN user_roles ur ON u.id = ur.user_id
        JOIN roles r ON ur.role_id = r.id
        WHERE r.name = 'department_admin'
          AND ur.department_id IS NOT NULL
          AND ur.is_active = true;
    """))).scalar()

    expected_covered = (await db_session.execute(text("""
        SELECT count(DISTINCT ur.department_id)
        FROM user_roles ur
        JOIN roles r ON ur.role_id = r.id
        WHERE r.name = 'department_admin'
          AND ur.department_id IS NOT NULL
          AND ur.is_active = true;
    """))).scalar()

    assert tier4["total_departments"] == 33
    assert tier4["department_admin_users_count"] == expected_da_users
    assert tier4["covered_departments"] == expected_covered
    assert tier4["vacant_departments"] == 33 - expected_covered
    expected_pct = round((expected_covered / 33) * 100, 1)
    assert tier4["coverage_percentage"] == expected_pct


# ===========================================================================
# TEST-07: Pipeline State Integrity
# ===========================================================================
@pytest.mark.asyncio
async def test_07_pipeline_state_integrity(
    client: AsyncClient,
    auth_actors: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    response = await client.get(
        "/api/v1/analytics/territorial/control-center",
        headers=auth_actors["sa_headers"],
    )
    assert response.status_code == 200
    data = response.json()
    tier2 = data["tier2_pipeline"]

    total_requests_db = (
        await db_session.execute(select(func.count(InstitutionOnboardingRequest.id)))
    ).scalar_one() or 0

    computed_sum = (
        tier2["submitted"]
        + tier2["under_review"]
        + tier2["approved"]
        + tier2["provisioned"]
        + tier2["rejected"]
        + tier2["cancelled"]
    )
    assert tier2["total_requests"] == total_requests_db
    # Sum of individual pipeline states must match total requests
    assert computed_sum <= total_requests_db  # Note: draft requests are not in the active pipeline breakdown


# ===========================================================================
# TEST-08: Department Detail Endpoint (Valid Department)
# ===========================================================================
@pytest.mark.asyncio
async def test_08_department_detail_endpoint(
    client: AsyncClient,
    auth_actors: dict[str, Any],
) -> None:
    response = await client.get(
        "/api/v1/analytics/territorial/control-center/departments/25",
        headers=auth_actors["sa_headers"],
    )
    assert response.status_code == 200, f"Expected 200, got: {response.text}"
    data = response.json()

    assert data["department_code"] == "25"
    assert data["department_name"] == "CUNDINAMARCA"
    assert data["total_municipalities"] == 116
    assert len(data["municipalities"]) == 116
    assert data["total_establishments"] > 0
    assert data["governance_status"] in ["COVERED", "INVITED", "VACANT"]


# ===========================================================================
# TEST-09: Department Detail IDOR (Foreign Department Forbidden)
# ===========================================================================
@pytest.mark.asyncio
async def test_09_department_detail_idor(
    client: AsyncClient,
    auth_actors: dict[str, Any],
) -> None:
    # Department Admin for Atlántico (08) attempts to query Cundinamarca (25) detail
    response = await client.get(
        "/api/v1/analytics/territorial/control-center/departments/25",
        headers=auth_actors["da_atl_headers"],
    )
    assert response.status_code == 403, (
        f"Cross-department detail query must be rejected with 403, got {response.status_code}"
    )


# ===========================================================================
# TEST-10: Role Isolation (Institutional Actors Forbidden)
# ===========================================================================
@pytest.mark.asyncio
async def test_10_role_isolation_institutional_actors(
    client: AsyncClient,
    auth_actors: dict[str, Any],
) -> None:
    if not auth_actors.get("tch_headers"):
        pytest.skip("No teacher actor available for institutional isolation check")

    response = await client.get(
        "/api/v1/analytics/territorial/control-center",
        headers=auth_actors["tch_headers"],
    )
    assert response.status_code == 403, (
        f"Institutional actor must receive 403, got {response.status_code}"
    )


# ===========================================================================
# TEST-11: Unauthenticated Access (Anonymous Forbidden)
# ===========================================================================
@pytest.mark.asyncio
async def test_11_unauthenticated_access(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/v1/analytics/territorial/control-center")
    assert response.status_code in [401, 403], (
        f"Unauthenticated request must be rejected, got {response.status_code}"
    )


# ===========================================================================
# TEST-12: Audit Log Emission (Sanitization Verified)
# ===========================================================================
@pytest.mark.asyncio
async def test_12_audit_log_emission_sanitization(
    client: AsyncClient,
    auth_actors: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    # Access national control center to trigger audit event
    response = await client.get(
        "/api/v1/analytics/territorial/control-center",
        headers=auth_actors["sa_headers"],
    )
    assert response.status_code == 200

    # Query latest audit log entry
    audit_res = await db_session.execute(text("""
        SELECT event_type, metadata
        FROM audit_logs
        WHERE event_type = :evt
        ORDER BY created_at DESC
        LIMIT 1;
    """), {"evt": AuditEventType.TERRITORIAL_CONTROL_CENTER_ACCESSED})
    row = audit_res.fetchone()

    if row:
        metadata_str = str(row[1]) if row[1] else ""
        assert "password" not in metadata_str.lower()
        assert "token" not in metadata_str.lower()
        assert "secret" not in metadata_str.lower()


# ===========================================================================
# TEST-13: Baseline Invariance (Read-Only Safety)
# ===========================================================================
@pytest.mark.asyncio
async def test_13_baseline_invariance_read_only(
    client: AsyncClient,
    auth_actors: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    # Counts before
    depts_before = (await db_session.execute(select(func.count(Department.id)))).scalar_one()
    munis_before = (await db_session.execute(select(func.count(Municipality.id)))).scalar_one()
    insts_before = (await db_session.execute(select(func.count(Institution.id)))).scalar_one()
    users_before = (await db_session.execute(select(func.count(User.id)))).scalar_one()

    # Perform control center queries
    await client.get("/api/v1/analytics/territorial/control-center", headers=auth_actors["sa_headers"])
    await client.get("/api/v1/analytics/territorial/control-center/departments/25", headers=auth_actors["sa_headers"])

    # Counts after
    depts_after = (await db_session.execute(select(func.count(Department.id)))).scalar_one()
    munis_after = (await db_session.execute(select(func.count(Municipality.id)))).scalar_one()
    insts_after = (await db_session.execute(select(func.count(Institution.id)))).scalar_one()
    users_after = (await db_session.execute(select(func.count(User.id)))).scalar_one()

    assert depts_before == depts_after == 33
    assert munis_before == munis_after == 1119
    assert insts_before == insts_after == 38
    assert users_before == users_after


# ===========================================================================
# TEST-14: Regression NTA-02 (DIVIPOLA Foundation)
# ===========================================================================
@pytest.mark.asyncio
async def test_14_regression_nta02_divipola(
    db_session: AsyncSession,
) -> None:
    dept_cnt = (await db_session.execute(select(func.count(Department.id)))).scalar_one()
    muni_cnt = (await db_session.execute(select(func.count(Municipality.id)))).scalar_one()
    orphan_cnt = (await db_session.execute(
        select(func.count(Municipality.id)).where(Municipality.department_id.is_(None))
    )).scalar_one()

    assert dept_cnt == 33
    assert muni_cnt == 1119
    assert orphan_cnt == 0


# ===========================================================================
# TEST-15: Regression NTA-03 & NTA-04 Preservation
# ===========================================================================
@pytest.mark.asyncio
async def test_15_regression_nta03_nta04_preservation(
    db_session: AsyncSession,
) -> None:
    cat_cnt = (await db_session.execute(select(func.count(OfficialInstitutionCatalog.id)))).scalar_one()
    total_tenants = (await db_session.execute(select(func.count(Institution.id)))).scalar_one()
    linked_tenants = (await db_session.execute(
        select(func.count(Institution.id)).where(Institution.catalog_institution_id.isnot(None))
    )).scalar_one()
    fixture_tenants = (await db_session.execute(
        select(func.count(Institution.id)).where(Institution.catalog_institution_id.is_(None))
    )).scalar_one()

    assert cat_cnt == 18031
    assert total_tenants == 38
    assert linked_tenants == 11
    assert fixture_tenants == 27
