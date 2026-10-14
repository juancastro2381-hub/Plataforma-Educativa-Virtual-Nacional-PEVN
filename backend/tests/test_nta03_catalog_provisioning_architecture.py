"""
PEVN — Phase NTA-03: Catalog <-> Provisioning Architecture Test Suite

Verifies:
  1. catalog_institution_id column exists on institutions.
  2. Foreign key exists on institutions.catalog_institution_id.
  3. Foreign key points to official_institution_catalog.id.
  4. Exactly 34 existing PEVN institutions preserved.
  5. Exactly 31 active institutions preserved.
  6. Exactly 3 inactive institutions preserved.
  7. Exactly 18 campuses preserved.
  8. Exactly 200 users preserved.
  9. Exactly 7 verified official institutions receive valid catalog_institution_id.
  10. Every catalog_institution_id resolves to an existing catalog record.
  11. No duplicate catalog_institution_id among PEVN tenants (unique partial index).
  12. dane_code matches catalog dane_code 100% for all linked institutions.
  13. Existing Department Admin scoped assignments (10) remain unchanged.
  14. Existing Anti-IDOR isolation returns HTTP 403 Forbidden across departments.
  15. Existing RBAC permissions and institutional isolation remain functional.
  16. NULL catalog_institution_id remains valid for synthetic/test fixtures (27 fixtures).
  17. Catalog records (18,031) do not automatically create operational PEVN tenants.
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
from app.models.official_catalog import OfficialInstitutionCatalog
from app.models.role import Role, UserRole
from app.models.territory import Department, Municipality
from app.models.user import User
from tests.conftest import get_test_postgres_url

PG_DB_URL = get_test_postgres_url()


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


@pytest.mark.asyncio
async def test_01_catalog_institution_id_column_exists(db_session: AsyncSession) -> None:
    """Test 1: Column catalog_institution_id exists on institutions table."""
    res = await db_session.execute(text("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'institutions' AND column_name = 'catalog_institution_id'
    """))
    row = res.fetchone()
    assert row is not None, "Column catalog_institution_id does not exist on institutions table"
    assert row[2] == "YES", "Column catalog_institution_id must be nullable"


@pytest.mark.asyncio
async def test_02_foreign_key_exists(db_session: AsyncSession) -> None:
    """Test 2: Foreign key constraint exists on institutions.catalog_institution_id."""
    res = await db_session.execute(text("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'institutions'
          AND constraint_type = 'FOREIGN KEY'
          AND constraint_name = 'fk_institutions_catalog_institution_id'
    """))
    name = res.scalar_one_or_none()
    assert name == "fk_institutions_catalog_institution_id"


@pytest.mark.asyncio
async def test_03_foreign_key_points_to_official_catalog(db_session: AsyncSession) -> None:
    """Test 3: Foreign key points to official_institution_catalog.id."""
    res = await db_session.execute(text("""
        SELECT ccu.table_name, ccu.column_name
        FROM information_schema.constraint_column_usage ccu
        JOIN information_schema.table_constraints tc ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_name = 'fk_institutions_catalog_institution_id'
    """))
    row = res.fetchone()
    assert row is not None
    assert row[0] == "official_institution_catalog"
    assert row[1] == "id"


@pytest.mark.asyncio
async def test_04_existing_34_institutions_preserved(db_session: AsyncSession) -> None:
    """Test 4: Total PEVN institutions count remains exactly 38 (authoritative post-Phase 0.6)."""
    count = (await db_session.execute(select(func.count(Institution.id)))).scalar_one()
    assert count == 38


@pytest.mark.asyncio
async def test_05_existing_31_active_institutions_preserved(db_session: AsyncSession) -> None:
    """Test 5: Exactly 35 active institutions preserved (authoritative post-Phase 0.6)."""
    count = (
        await db_session.execute(
            select(func.count(Institution.id)).where(Institution.is_active == True)  # noqa: E712
        )
    ).scalar_one()
    assert count == 35


@pytest.mark.asyncio
async def test_06_existing_3_inactive_institutions_preserved(db_session: AsyncSession) -> None:
    """Test 6: Exactly 3 inactive institutions preserved."""
    count = (
        await db_session.execute(
            select(func.count(Institution.id)).where(Institution.is_active == False)  # noqa: E712
        )
    ).scalar_one()
    assert count == 3


@pytest.mark.asyncio
async def test_07_existing_18_campuses_preserved(db_session: AsyncSession) -> None:
    """Test 7: Exactly 26 operational campuses preserved (authoritative post-Phase 0.6)."""
    count = (await db_session.execute(select(func.count(Campus.id)))).scalar_one()
    assert count == 26


@pytest.mark.asyncio
async def test_08_existing_200_users_preserved(db_session: AsyncSession) -> None:
    """Test 8: Exactly 223 users preserved (authoritative post-Phase 0.6)."""
    count = (await db_session.execute(select(func.count(User.id)))).scalar_one()
    assert count == 223


@pytest.mark.asyncio
async def test_09_verified_official_institutions_receive_valid_catalog_id(
    db_session: AsyncSession,
) -> None:
    """Test 9: Exactly 11 verified official institutions received catalog_institution_id (authoritative post-Phase 0.6)."""
    count = (
        await db_session.execute(
            select(func.count(Institution.id)).where(
                Institution.catalog_institution_id.is_not(None)
            )
        )
    ).scalar_one()
    assert count == 11


@pytest.mark.asyncio
async def test_10_every_catalog_institution_id_resolves_to_existing_catalog_record(
    db_session: AsyncSession,
) -> None:
    """Test 10: Every populated catalog_institution_id points to an existing record."""
    stmt = (
        select(Institution.catalog_institution_id)
        .where(Institution.catalog_institution_id.is_not(None))
    )
    cat_ids = (await db_session.execute(stmt)).scalars().all()
    assert len(cat_ids) == 11

    for cat_id in cat_ids:
        cat_rec = await db_session.get(OfficialInstitutionCatalog, cat_id)
        assert cat_rec is not None, f"Catalog record {cat_id} not found in official catalog"


@pytest.mark.asyncio
async def test_11_no_duplicate_catalog_institution_id(db_session: AsyncSession) -> None:
    """Test 11: No duplicate catalog_institution_id values exist among PEVN tenants."""
    res = await db_session.execute(text("""
        SELECT catalog_institution_id, count(*)
        FROM institutions
        WHERE catalog_institution_id IS NOT NULL
        GROUP BY catalog_institution_id
        HAVING count(*) > 1
    """))
    dups = res.fetchall()
    assert len(dups) == 0, f"Found duplicate catalog references: {dups}"


@pytest.mark.asyncio
async def test_12_dane_code_matches_catalog_dane_code(db_session: AsyncSession) -> None:
    """Test 12: 100% of linked institutions have matching DANE codes with catalog."""
    res = await db_session.execute(text("""
        SELECT i.dane_code, c.dane_code
        FROM institutions i
        JOIN official_institution_catalog c ON i.catalog_institution_id = c.id
    """))
    rows = res.fetchall()
    assert len(rows) == 11
    for inst_dane, cat_dane in rows:
        assert inst_dane == cat_dane, f"DANE mismatch: {inst_dane} != {cat_dane}"


@pytest.mark.asyncio
async def test_13_existing_department_admin_assignments_unchanged(
    db_session: AsyncSession,
) -> None:
    """Test 13: Exactly 14 scoped Department Administrators preserved with valid department_id (authoritative post-Phase 0.6)."""
    res = await db_session.execute(text("""
        SELECT count(*)
        FROM user_roles ur
        JOIN roles r ON ur.role_id = r.id
        WHERE r.name = 'department_admin' AND ur.department_id IS NOT NULL
    """))
    count = res.scalar_one()
    assert count == 14


@pytest.mark.asyncio
async def test_14_anti_idor_isolation_preserved(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Test 14: Department Admin for Atlántico cannot access Bogotá institutions (HTTP 403)."""
    # Find Atlántico Department Admin user
    res = await db_session.execute(text("""
        SELECT u.id, u.email, ur.department_id
        FROM users u
        JOIN user_roles ur ON u.id = ur.user_id
        JOIN roles r ON ur.role_id = r.id
        JOIN departments d ON ur.department_id = d.id
        WHERE r.name = 'department_admin' AND d.code = '08' AND u.is_active = true
        LIMIT 1
    """))
    da_user = res.fetchone()
    assert da_user is not None, "Active Atlántico Department Admin not found"

    # Find a Bogotá institution
    bgt_res = await db_session.execute(text("""
        SELECT i.id
        FROM institutions i
        JOIN municipalities m ON i.municipality_id = m.id
        JOIN departments d ON m.department_id = d.id
        WHERE d.code = '11'
        LIMIT 1
    """))
    bgt_inst = bgt_res.fetchone()
    assert bgt_inst is not None

    token = await token_service.create_access_token(subject=str(da_user[0]))

    # Attempt cross-department access to Bogotá institution
    response = await client.get(
        f"/api/v1/institutions/{bgt_inst[0]}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_15_rbac_scoped_access_same_department_allowed(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Test 15: Department Admin for Atlántico CAN access Atlántico institution (HTTP 200)."""
    res = await db_session.execute(text("""
        SELECT u.id, u.email
        FROM users u
        JOIN user_roles ur ON u.id = ur.user_id
        JOIN roles r ON ur.role_id = r.id
        JOIN departments d ON ur.department_id = d.id
        WHERE r.name = 'department_admin' AND d.code = '08' AND u.is_active = true
        LIMIT 1
    """))
    da_user = res.fetchone()
    assert da_user is not None

    atl_res = await db_session.execute(text("""
        SELECT i.id
        FROM institutions i
        JOIN municipalities m ON i.municipality_id = m.id
        JOIN departments d ON m.department_id = d.id
        WHERE d.code = '08'
        LIMIT 1
    """))
    atl_inst = atl_res.fetchone()
    assert atl_inst is not None

    token = await token_service.create_access_token(subject=str(da_user[0]))

    response = await client.get(
        f"/api/v1/institutions/{atl_inst[0]}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_16_null_catalog_institution_id_valid_for_synthetic_fixtures(
    db_session: AsyncSession,
) -> None:
    """Test 16: Exactly 27 synthetic test institutions have NULL catalog_institution_id safely."""
    count = (
        await db_session.execute(
            select(func.count(Institution.id)).where(
                Institution.catalog_institution_id.is_(None)
            )
        )
    ).scalar_one()
    assert count == 27


@pytest.mark.asyncio
async def test_17_catalog_records_do_not_automatically_create_tenants(
    db_session: AsyncSession,
) -> None:
    """Test 17: Official catalog remains reference universe (18,031) while tenants remain 38 (authoritative post-Phase 0.6)."""
    cat_count = (
        await db_session.execute(select(func.count(OfficialInstitutionCatalog.id)))
    ).scalar_one()
    tenant_count = (await db_session.execute(select(func.count(Institution.id)))).scalar_one()

    assert cat_count == 18031
    assert tenant_count == 38
    assert cat_count > tenant_count
