"""
PEVN — Phase NTA-02: National DIVIPOLA Operational Foundation Test Suite

Verifies:
  1. 33 operational departments exist in departments table.
  2. 1,119 operational municipalities exist in municipalities table.
  3. Unique department DANE codes across all 33 records.
  4. Unique municipality DANE codes across all 1,119 records.
  5. Every municipality references an existing parent department.
  6. Existing pilot department UUIDs (08, 11, 25) are preserved.
  7. Existing pilot municipality UUIDs (08001, 11001, 25286) are preserved.
  8. Exactly 38 existing PEVN institutions preserved.
  9. Exactly 35 active institutions preserved.
  10. Exactly 3 inactive institutions preserved.
  11. Existing institution -> municipality foreign keys preserved.
  12. Existing Department Admin -> department assignments preserved.
  13. Zero-tenant departments are valid operational state.
  14. Zero-tenant municipalities are valid operational state.
  15. Department API (GET /api/v1/departments) exposes all 33 territories.
  16. Department-scoped users cannot access another department (Anti-IDOR HTTP 403).
  17. Existing Anti-IDOR regression verification.
"""

from collections.abc import AsyncGenerator
import uuid
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.security.tokens import token_service
from app.db.session import get_async_session
from app.main import create_application
from app.models.institution import Campus, Institution
from app.models.role import Role, UserRole
from app.models.territory import Department, Municipality
from app.models.user import User

from tests.conftest import get_test_postgres_url

PG_DB_URL = get_test_postgres_url()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated session connected to the isolated test PostgreSQL database (pevn_test_db)."""
    engine = create_async_engine(PG_DB_URL, poolclass=NullPool)
    session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async test client connected to the PostgreSQL database."""
    test_app = create_application()

    async def _override_get_async_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    test_app.dependency_overrides[get_async_session] = _override_get_async_session

    async with AsyncClient(
        transport=ASGITransport(app=test_app),  # type: ignore[arg-type]
        base_url="http://localhost",
        headers={"Host": "localhost"},
    ) as test_client:
        yield test_client


PILOT_DEPT_UUIDS = {
    "08": uuid.UUID("caf3cc3f-a895-4fcd-b4b9-17405f3edf76"),
    "11": uuid.UUID("7b774116-56f1-4199-ac63-ff646e7e327b"),
    "25": uuid.UUID("9aea113f-54e2-4345-8cc6-46970a91c7c6"),
}

PILOT_MUNI_UUIDS = {
    "08001": uuid.UUID("709359d8-4c2f-4d90-be5d-2140a5ff458e"),
    "11001": uuid.UUID("75495d0b-e2f0-4d1b-9114-02589135a863"),
    "25286": uuid.UUID("63d46e72-6f03-4785-a2f0-4becf6a56134"),
}


@pytest.mark.asyncio
async def test_01_thirty_three_departments_exist(db_session: AsyncSession) -> None:
    """Invariant 1: Exactly 33 operational departments exist."""
    count = (await db_session.execute(select(func.count(Department.id)))).scalar_one()
    assert count == 33


@pytest.mark.asyncio
async def test_02_one_thousand_one_hundred_nineteen_municipalities_exist(
    db_session: AsyncSession,
) -> None:
    """Invariant 2: Exactly 1,119 operational municipalities exist."""
    count = (await db_session.execute(select(func.count(Municipality.id)))).scalar_one()
    assert count == 1119


@pytest.mark.asyncio
async def test_03_unique_department_dane_codes(db_session: AsyncSession) -> None:
    """Invariant 3: All department codes are strictly unique."""
    distinct_codes = (
        await db_session.execute(select(func.count(func.distinct(Department.code))))
    ).scalar_one()
    total_count = (await db_session.execute(select(func.count(Department.id)))).scalar_one()
    assert distinct_codes == total_count == 33


@pytest.mark.asyncio
async def test_04_unique_municipality_dane_codes(db_session: AsyncSession) -> None:
    """Invariant 4: All municipality codes are strictly unique."""
    distinct_codes = (
        await db_session.execute(select(func.count(func.distinct(Municipality.code))))
    ).scalar_one()
    total_count = (
        await db_session.execute(select(func.count(Municipality.id)))
    ).scalar_one()
    assert distinct_codes == total_count == 1119


@pytest.mark.asyncio
async def test_05_every_municipality_references_existing_department(
    db_session: AsyncSession,
) -> None:
    """Invariant 5: Every municipality references an existing department with zero orphans."""
    orphan_query = text(
        "SELECT count(*) FROM municipalities m "
        "LEFT JOIN departments d ON m.department_id = d.id "
        "WHERE d.id IS NULL;"
    )
    orphan_count = (await db_session.execute(orphan_query)).scalar()
    assert orphan_count == 0


@pytest.mark.asyncio
async def test_06_pilot_department_uuids_preserved(db_session: AsyncSession) -> None:
    """Invariant 6: Pilot department UUIDs (08, 11, 25) remain 100% unchanged."""
    for code, expected_uuid in PILOT_DEPT_UUIDS.items():
        dept = (
            await db_session.execute(select(Department).where(Department.code == code))
        ).scalar_one_or_none()
        assert dept is not None, f"Department {code} missing"
        assert dept.id == expected_uuid, f"Department {code} UUID changed"


@pytest.mark.asyncio
async def test_07_pilot_municipality_uuids_preserved(db_session: AsyncSession) -> None:
    """Invariant 7: Pilot municipality UUIDs (08001, 11001, 25286) remain 100% unchanged."""
    for code, expected_uuid in PILOT_MUNI_UUIDS.items():
        muni = (
            await db_session.execute(
                select(Municipality).where(Municipality.code == code)
            )
        ).scalar_one_or_none()
        assert muni is not None, f"Municipality {code} missing"
        assert muni.id == expected_uuid, f"Municipality {code} UUID changed"


@pytest.mark.asyncio
async def test_08_thirty_eight_institutions_preserved(db_session: AsyncSession) -> None:
    """Invariant 8: Exactly 38 institutions preserved (authoritative post-Phase 0.6)."""
    count = (await db_session.execute(select(func.count(Institution.id)))).scalar_one()
    assert count == 38


@pytest.mark.asyncio
async def test_09_thirty_five_active_institutions_preserved(
    db_session: AsyncSession,
) -> None:
    """Invariant 9: Exactly 35 active institutions preserved (authoritative post-Phase 0.6)."""
    count = (
        await db_session.execute(
            select(func.count(Institution.id)).where(Institution.is_active == True)
        )
    ).scalar_one()
    assert count == 35


@pytest.mark.asyncio
async def test_10_three_inactive_institutions_preserved(
    db_session: AsyncSession,
) -> None:
    """Invariant 10: Exactly 3 inactive institutions preserved."""
    count = (
        await db_session.execute(
            select(func.count(Institution.id)).where(Institution.is_active == False)
        )
    ).scalar_one()
    assert count == 3


@pytest.mark.asyncio
async def test_11_institution_municipality_fks_preserved(
    db_session: AsyncSession,
) -> None:
    """Invariant 11: All institutions reference valid existing municipalities."""
    invalid_fks = (
        await db_session.execute(
            text(
                "SELECT count(*) FROM institutions i "
                "LEFT JOIN municipalities m ON i.municipality_id = m.id "
                "WHERE m.id IS NULL;"
            )
        )
    ).scalar()
    assert invalid_fks == 0


@pytest.mark.asyncio
async def test_12_department_admin_assignments_preserved(
    db_session: AsyncSession,
) -> None:
    """Invariant 12: Exactly 14 scoped department_admin assignments preserved (authoritative post-Phase 0.6)."""
    da_role = (
        await db_session.execute(select(Role).where(Role.name == "department_admin"))
    ).scalar_one()
    scoped_das = (
        await db_session.execute(
            select(func.count(UserRole.id)).where(
                UserRole.role_id == da_role.id,
                UserRole.department_id.is_not(None),
            )
        )
    ).scalar_one()
    assert scoped_das == 14


@pytest.mark.asyncio
async def test_13_zero_tenant_departments_are_valid(db_session: AsyncSession) -> None:
    """Invariant 13: Exactly 28 departments have 0 PEVN tenants and are valid (authoritative post-Phase 0.6)."""
    zero_tenant_query = text(
        "SELECT count(*) FROM departments d "
        "LEFT JOIN municipalities m ON m.department_id = d.id "
        "LEFT JOIN institutions i ON i.municipality_id = m.id "
        "GROUP BY d.id "
        "HAVING count(i.id) = 0;"
    )
    zero_depts = (await db_session.execute(zero_tenant_query)).all()
    assert len(zero_depts) == 28


@pytest.mark.asyncio
async def test_14_zero_tenant_municipalities_are_valid(
    db_session: AsyncSession,
) -> None:
    """Invariant 14: Over 1,110 municipalities have 0 PEVN tenants and are valid (authoritative post-Phase 0.6)."""
    zero_muni_query = text(
        "SELECT count(*) FROM municipalities m "
        "LEFT JOIN institutions i ON i.municipality_id = m.id "
        "WHERE i.id IS NULL;"
    )
    zero_munis = (await db_session.execute(zero_muni_query)).scalar()
    assert zero_munis == 1113  # 1119 - 6 municipalities with institutions


@pytest.mark.asyncio
async def test_15_department_api_exposes_all_thirty_three_departments(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Invariant 15: GET /api/v1/departments returns 33 departments with canonical labels."""
    superadmin_id = (
        await db_session.execute(
            select(User.id)
            .join(UserRole, User.id == UserRole.user_id)
            .join(Role, UserRole.role_id == Role.id)
            .where(Role.name == "superadmin", User.is_active == True)
            .limit(1)
        )
    ).scalar_one()

    token = await token_service.create_access_token(subject=str(superadmin_id))
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/departments", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 33

    codes = [d["code"] for d in data]
    for check_code in ["05", "08", "11", "25", "76", "91", "99"]:
        assert check_code in codes


@pytest.mark.asyncio
async def test_16_department_admin_cannot_access_another_department(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Invariant 16: Atlántico Department Admin cannot access Bogotá institution (HTTP 403)."""
    # Atlántico DA
    da_user_id = (
        await db_session.execute(
            select(User.id).where(User.username == "Eduardo_Admin_Departamental")
        )
    ).scalar_one()
    token = await token_service.create_access_token(subject=str(da_user_id))
    headers = {"Authorization": f"Bearer {token}"}

    # Bogotá institution
    bogota_inst_id = (
        await db_session.execute(
            select(Institution.id)
            .join(Municipality, Institution.municipality_id == Municipality.id)
            .join(Department, Municipality.department_id == Department.id)
            .where(Department.code == "11")
            .limit(1)
        )
    ).scalar_one()

    # Atlántico institution
    atlantico_inst_id = (
        await db_session.execute(
            select(Institution.id)
            .join(Municipality, Institution.municipality_id == Municipality.id)
            .join(Department, Municipality.department_id == Department.id)
            .where(Department.code == "08")
            .limit(1)
        )
    ).scalar_one()

    # Own department institution -> HTTP 200
    res_own = await client.get(
        f"/api/v1/institutions/{atlantico_inst_id}", headers=headers
    )
    assert res_own.status_code == 200

    # Cross-department institution -> HTTP 403 Forbidden
    res_cross = await client.get(
        f"/api/v1/institutions/{bogota_inst_id}", headers=headers
    )
    assert res_cross.status_code == 403


@pytest.mark.asyncio
async def test_17_national_analytics_summary_reflects_thirty_three_departments(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Invariant 17: Territorial summary reports 33 departments and 1,119 municipalities."""
    superadmin_id = (
        await db_session.execute(
            select(User.id)
            .join(UserRole, User.id == UserRole.user_id)
            .join(Role, UserRole.role_id == Role.id)
            .where(Role.name == "superadmin", User.is_active == True)
            .limit(1)
        )
    ).scalar_one()

    token = await token_service.create_access_token(subject=str(superadmin_id))
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/v1/analytics/territorial/summary", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_departments"] == 33
    assert data["total_municipalities"] == 1119
    assert data["provisioned_institutions"] == 35
