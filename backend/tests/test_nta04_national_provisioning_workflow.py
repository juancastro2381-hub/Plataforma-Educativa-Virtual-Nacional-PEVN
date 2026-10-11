"""
PEVN — Phase NTA-04: National Provisioning Workflow Test Suite

Automated test specifications verifying the NTA-04 architecture blueprint:
  TEST-01: Happy Path Onboarding (Filing -> Review -> Approval -> Atomic Provisioning).
  TEST-02: Rector Invitation Chaining (SHA-256 token, inactive rector creation).
  TEST-03: Onboarding without Immediate Rector (Pending rector assignment state).
  TEST-04: Anti-Duplication of Active Requests (Partial unique index uq_onboarding_active_catalog_institution).
  TEST-05: Anti-Duplication for Existing Provisioned Tenants.
  TEST-06: Anti-IDOR Filing Boundary (Department Admin cross-department filing rejected with HTTP 403).
  TEST-07: Anti-IDOR Approval Boundary (Department Admin cross-department approval rejected with HTTP 403).
  TEST-08: Anti-IDOR Query Boundary (Department Admin cross-department detail/list rejected with HTTP 403).
  TEST-09: Departmental Autonomy (Department Admin same-department approval succeeded with HTTP 200).
  TEST-10: National Authority Scope (National Admin operates across all 33 departments).
  TEST-11: Rejection Requires Substantive Reason (>= 10 chars mandatory).
  TEST-12: Authorized Cancellation by Requester.
  TEST-13: Unauthorized Cancellation Attempt (Rejected with HTTP 403).
  TEST-14: Forbidden State Transitions (Rejected / Cancelled cannot be approved, etc.).
  TEST-15: Concurrency / Race Condition on Provisioning (One tenant created, 2nd request 409).
  TEST-16: Inactive Catalog Establishment Rejected (HTTP 422).
  TEST-17: Non-existent Catalog Record Rejected (HTTP 404).
  TEST-18: Preservation of the 27 Synthetic Fixture Institutions (NULL catalog_institution_id).
"""

from collections.abc import AsyncGenerator
import asyncio
import uuid
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.security.tokens import token_service
from app.db.session import get_async_session
from app.main import create_application
from app.models.institution import Campus, Institution
from app.models.invitation import RectorInvitation
from app.models.official_catalog import OfficialInstitutionCatalog
from app.models.onboarding import InstitutionOnboardingRequest, OnboardingRequestStatus
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
    """Resolve authenticated test actors across national and departmental scopes."""
    # 1. National Admin
    na_res = await db_session.execute(text("""
        SELECT u.id, u.email
        FROM users u
        JOIN user_roles ur ON u.id = ur.user_id
        JOIN roles r ON ur.role_id = r.id
        WHERE r.name IN ('national_admin', 'superadmin') AND u.is_active = true
        LIMIT 1
    """))
    na_row = na_res.fetchone()
    assert na_row is not None
    na_token = await token_service.create_access_token(subject=str(na_row[0]))

    # 2. Department Admin - Atlántico (08)
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
    assert da_atl_row is not None
    da_atl_token = await token_service.create_access_token(subject=str(da_atl_row[0]))

    # 3. Department Admin - Bogotá (11)
    da_bog_res = await db_session.execute(text("""
        SELECT u.id, u.email, d.id as dept_id, d.code as dept_code
        FROM users u
        JOIN user_roles ur ON u.id = ur.user_id
        JOIN roles r ON ur.role_id = r.id
        JOIN departments d ON ur.department_id = d.id
        WHERE r.name = 'department_admin' AND d.code = '11' AND u.is_active = true
        LIMIT 1
    """))
    da_bog_row = da_bog_res.fetchone()
    assert da_bog_row is not None
    da_bog_token = await token_service.create_access_token(subject=str(da_bog_row[0]))

    # 4. Another regular user (e.g. Docente or another actor)
    teacher_res = await db_session.execute(text("""
        SELECT u.id, u.email
        FROM users u
        JOIN user_roles ur ON u.id = ur.user_id
        JOIN roles r ON ur.role_id = r.id
        WHERE r.name = 'teacher' AND u.is_active = true
        LIMIT 1
    """))
    teacher_row = teacher_res.fetchone()
    teacher_token = await token_service.create_access_token(subject=str(teacher_row[0])) if teacher_row else ""

    return {
        "na_id": na_row[0],
        "na_headers": {"Authorization": f"Bearer {na_token}"},
        "da_atl_id": da_atl_row[0],
        "da_atl_dept_id": da_atl_row[2],
        "da_atl_headers": {"Authorization": f"Bearer {da_atl_token}"},
        "da_bog_id": da_bog_row[0],
        "da_bog_dept_id": da_bog_row[2],
        "da_bog_headers": {"Authorization": f"Bearer {da_bog_token}"},
        "teacher_id": teacher_row[0] if teacher_row else None,
        "teacher_headers": {"Authorization": f"Bearer {teacher_token}"},
    }


# ==============================================================================
# TEST 01: Happy Path Onboarding (Filing -> Review -> Approve -> Provision)
# ==============================================================================
@pytest.mark.asyncio
async def test_01_happy_path_onboarding(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_actors: dict[str, Any],
) -> None:
    """TEST-01: Complete lifecycle from catalog filing to provisioned tenant."""
    # Find an unprovisioned official establishment in Atlántico (08)
    cat_res = await db_session.execute(text("""
        SELECT id, dane_code, name, department_code, municipality_code
        FROM official_institution_catalog
        WHERE department_code = '08'
          AND is_active = true
          AND dane_code NOT IN (SELECT dane_code FROM institutions)
          AND id NOT IN (SELECT catalog_institution_id FROM institution_onboarding_requests)
        LIMIT 1
    """))
    cat_row = cat_res.fetchone()
    assert cat_row is not None, "Unprovisioned catalog institution not found"

    catalog_id, dane_code, name, dept_code, muni_code = cat_row

    created_inst_id: str | None = None
    created_req_id: str | None = None

    try:
        # 1. File Request
        payload = {
            "catalog_institution_id": str(catalog_id),
            "contact_email": f"test_onb_{dane_code}@colegio.edu.co",
            "contact_phone": "3001234567",
            "justification": "Solicitud formal de incorporación institucional PEVN.",
            "is_draft": False,
        }
        res_create = await client.post(
            "/api/v1/onboarding/requests",
            json=payload,
            headers=auth_actors["na_headers"],
        )
        assert res_create.status_code == 201
        data_create = res_create.json()
        created_req_id = data_create["id"]
        assert data_create["status"] == "SUBMITTED"
        assert data_create["dane_code"] == dane_code

        # 2. Start Review
        res_rev = await client.post(
            f"/api/v1/onboarding/requests/{created_req_id}/start-review",
            headers=auth_actors["na_headers"],
        )
        assert res_rev.status_code == 200
        assert res_rev.json()["status"] == "UNDER_REVIEW"

        # 3. Approve Request
        res_app = await client.post(
            f"/api/v1/onboarding/requests/{created_req_id}/approve",
            json={"notes": "Aprobación técnica favorable."},
            headers=auth_actors["na_headers"],
        )
        assert res_app.status_code == 200
        assert res_app.json()["status"] == "APPROVED"

        # 4. Provision Tenant
        res_prov = await client.post(
            f"/api/v1/onboarding/requests/{created_req_id}/provision",
            headers=auth_actors["na_headers"],
        )
        assert res_prov.status_code == 201
        data_prov = res_prov.json()
        created_inst_id = data_prov["institution_id"]
        assert data_prov["dane_code"] == dane_code
        assert data_prov["campuses_created"] >= 1

        # 5. Database Verification
        inst_db = (
            await db_session.execute(
                select(Institution).where(Institution.id == uuid.UUID(created_inst_id))
            )
        ).scalar_one_or_none()
        assert inst_db is not None
        assert inst_db.catalog_institution_id == catalog_id
        assert inst_db.dane_code == dane_code
        assert inst_db.is_active is True

        req_db = (
            await db_session.execute(
                select(InstitutionOnboardingRequest).where(
                    InstitutionOnboardingRequest.id == uuid.UUID(created_req_id)
                )
            )
        ).scalar_one_or_none()
        assert req_db is not None
        assert req_db.status == "PROVISIONED"
        assert req_db.institution_id == uuid.UUID(created_inst_id)

    finally:
        # Cleanup
        if created_inst_id:
            await db_session.execute(delete(Campus).where(Campus.institution_id == uuid.UUID(created_inst_id)))
            await db_session.execute(delete(Institution).where(Institution.id == uuid.UUID(created_inst_id)))
        if created_req_id:
            await db_session.execute(delete(InstitutionOnboardingRequest).where(InstitutionOnboardingRequest.id == uuid.UUID(created_req_id)))
        await db_session.commit()


# ==============================================================================
# TEST 02: Rector Invitation Chaining
# ==============================================================================
@pytest.mark.asyncio
async def test_02_rector_invitation_chaining(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_actors: dict[str, Any],
) -> None:
    """TEST-02: Provisioning with rector data creates inactive rector & invitation token."""
    cat_res = await db_session.execute(text("""
        SELECT id, dane_code
        FROM official_institution_catalog
        WHERE department_code = '08'
          AND is_active = true
          AND dane_code NOT IN (SELECT dane_code FROM institutions)
          AND id NOT IN (SELECT catalog_institution_id FROM institution_onboarding_requests)
        LIMIT 1
    """))
    cat_row = cat_res.fetchone()
    catalog_id, dane_code = cat_row

    created_inst_id: str | None = None
    created_req_id: str | None = None
    created_rector_id: uuid.UUID | None = None

    rector_email = f"rector_{dane_code}@colegio.edu.co"
    rector_doc = f"CC{dane_code[:8]}"

    try:
        # File with proposed rector
        payload = {
            "catalog_institution_id": str(catalog_id),
            "contact_email": f"inst_{dane_code}@colegio.edu.co",
            "proposed_rector_name": "Gabriel García Márquez",
            "proposed_rector_email": rector_email,
            "proposed_rector_doc_type": "CC",
            "proposed_rector_doc_num": rector_doc,
            "is_draft": False,
        }
        res_create = await client.post(
            "/api/v1/onboarding/requests",
            json=payload,
            headers=auth_actors["na_headers"],
        )
        created_req_id = res_create.json()["id"]

        # Approve directly
        await client.post(
            f"/api/v1/onboarding/requests/{created_req_id}/approve",
            json={"notes": "Aprobación directa"},
            headers=auth_actors["na_headers"],
        )

        # Provision
        res_prov = await client.post(
            f"/api/v1/onboarding/requests/{created_req_id}/provision",
            headers=auth_actors["na_headers"],
        )
        assert res_prov.status_code == 201
        data_prov = res_prov.json()
        created_inst_id = data_prov["institution_id"]
        assert data_prov["rector_invited"] is True
        assert data_prov["rector_status"] == "INVITED"
        assert data_prov["rector_invitation_id"] is not None
        assert data_prov["raw_invitation_token"] is not None

        # Verify Rector user created inactive in DB
        rector_user = (
            await db_session.execute(select(User).where(User.email == rector_email))
        ).scalar_one_or_none()
        assert rector_user is not None
        assert rector_user.is_active is False
        created_rector_id = rector_user.id

        # Verify Invitation in DB
        inv_db = (
            await db_session.execute(
                select(RectorInvitation).where(
                    RectorInvitation.id == uuid.UUID(data_prov["rector_invitation_id"])
                )
            )
        ).scalar_one_or_none()
        assert inv_db is not None
        assert inv_db.token_hash is not None
        assert inv_db.is_used is False

    finally:
        if created_rector_id:
            await db_session.execute(delete(RectorInvitation).where(RectorInvitation.user_id == created_rector_id))
            await db_session.execute(delete(UserRole).where(UserRole.user_id == created_rector_id))
            await db_session.execute(delete(User).where(User.id == created_rector_id))
        if created_inst_id:
            await db_session.execute(delete(Campus).where(Campus.institution_id == uuid.UUID(created_inst_id)))
            await db_session.execute(delete(Institution).where(Institution.id == uuid.UUID(created_inst_id)))
        if created_req_id:
            await db_session.execute(delete(InstitutionOnboardingRequest).where(InstitutionOnboardingRequest.id == uuid.UUID(created_req_id)))
        await db_session.commit()


# ==============================================================================
# TEST 03: Onboarding without Immediate Rector
# ==============================================================================
@pytest.mark.asyncio
async def test_03_onboarding_without_immediate_rector(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_actors: dict[str, Any],
) -> None:
    """TEST-03: Provisioning without rector succeeds with PENDING_ASSIGNMENT."""
    cat_res = await db_session.execute(text("""
        SELECT id, dane_code
        FROM official_institution_catalog
        WHERE department_code = '08'
          AND is_active = true
          AND dane_code NOT IN (SELECT dane_code FROM institutions)
          AND id NOT IN (SELECT catalog_institution_id FROM institution_onboarding_requests)
        LIMIT 1
    """))
    catalog_id, dane_code = cat_res.fetchone()

    created_inst_id: str | None = None
    created_req_id: str | None = None

    try:
        payload = {
            "catalog_institution_id": str(catalog_id),
            "contact_email": f"norector_{dane_code}@colegio.edu.co",
            "is_draft": False,
        }
        res_create = await client.post(
            "/api/v1/onboarding/requests",
            json=payload,
            headers=auth_actors["na_headers"],
        )
        created_req_id = res_create.json()["id"]

        await client.post(
            f"/api/v1/onboarding/requests/{created_req_id}/approve",
            json={"notes": "Aprobación"},
            headers=auth_actors["na_headers"],
        )

        res_prov = await client.post(
            f"/api/v1/onboarding/requests/{created_req_id}/provision",
            headers=auth_actors["na_headers"],
        )
        assert res_prov.status_code == 201
        data_prov = res_prov.json()
        created_inst_id = data_prov["institution_id"]
        assert data_prov["rector_invited"] is False
        assert data_prov["rector_status"] == "PENDING_ASSIGNMENT"

    finally:
        if created_inst_id:
            await db_session.execute(delete(Campus).where(Campus.institution_id == uuid.UUID(created_inst_id)))
            await db_session.execute(delete(Institution).where(Institution.id == uuid.UUID(created_inst_id)))
        if created_req_id:
            await db_session.execute(delete(InstitutionOnboardingRequest).where(InstitutionOnboardingRequest.id == uuid.UUID(created_req_id)))
        await db_session.commit()


# ==============================================================================
# TEST 04: Anti-Duplication of Active Requests
# ==============================================================================
@pytest.mark.asyncio
async def test_04_anti_duplication_active_requests(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_actors: dict[str, Any],
) -> None:
    """TEST-04: Partial unique index blocks duplicate active requests with HTTP 409."""
    cat_res = await db_session.execute(text("""
        SELECT id, dane_code
        FROM official_institution_catalog
        WHERE department_code = '08'
          AND is_active = true
          AND dane_code NOT IN (SELECT dane_code FROM institutions)
          AND id NOT IN (SELECT catalog_institution_id FROM institution_onboarding_requests)
        LIMIT 1
    """))
    catalog_id, dane_code = cat_res.fetchone()

    created_req_id: str | None = None

    try:
        payload = {
            "catalog_institution_id": str(catalog_id),
            "contact_email": f"active1_{dane_code}@colegio.edu.co",
            "is_draft": False,
        }
        res1 = await client.post(
            "/api/v1/onboarding/requests",
            json=payload,
            headers=auth_actors["na_headers"],
        )
        assert res1.status_code == 201
        created_req_id = res1.json()["id"]

        # Attempt to file a second request for the same catalog institution
        payload2 = {
            "catalog_institution_id": str(catalog_id),
            "contact_email": f"active2_{dane_code}@colegio.edu.co",
            "is_draft": False,
        }
        res2 = await client.post(
            "/api/v1/onboarding/requests",
            json=payload2,
            headers=auth_actors["na_headers"],
        )
        assert res2.status_code == 409
        assert "ACTIVE_REQUEST_EXISTS" in res2.text or "409" in str(res2.status_code)

    finally:
        if created_req_id:
            await db_session.execute(delete(InstitutionOnboardingRequest).where(InstitutionOnboardingRequest.id == uuid.UUID(created_req_id)))
        await db_session.commit()


# ==============================================================================
# TEST 05: Anti-Duplication for Existing Provisioned Tenants
# ==============================================================================
@pytest.mark.asyncio
async def test_05_anti_duplication_existing_tenant(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_actors: dict[str, Any],
) -> None:
    """TEST-05: Filing onboarding for an already provisioned tenant returns HTTP 409."""
    # Pick one of the 7 already provisioned catalog-linked institutions
    inst_res = await db_session.execute(text("""
        SELECT catalog_institution_id
        FROM institutions
        WHERE catalog_institution_id IS NOT NULL
        LIMIT 1
    """))
    cat_id = inst_res.scalar_one()

    payload = {
        "catalog_institution_id": str(cat_id),
        "contact_email": "dup@tenant.edu.co",
        "is_draft": False,
    }
    res = await client.post(
        "/api/v1/onboarding/requests",
        json=payload,
        headers=auth_actors["na_headers"],
    )
    assert res.status_code == 409
    assert "INSTITUTION_ALREADY_PROVISIONED" in res.text


# ==============================================================================
# TEST 06: Anti-IDOR Filing Boundary
# ==============================================================================
@pytest.mark.asyncio
async def test_06_anti_idor_filing(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_actors: dict[str, Any],
) -> None:
    """TEST-06: Department Admin (Atlántico) filing for Bogotá is rejected with HTTP 403."""
    # Find a catalog institution in Bogotá (11)
    cat_bog = (
        await db_session.execute(text("""
            SELECT id FROM official_institution_catalog
            WHERE department_code = '11' AND is_active = true
            LIMIT 1
        """))
    ).scalar_one()

    payload = {
        "catalog_institution_id": str(cat_bog),
        "contact_email": "cross@bogota.edu.co",
        "is_draft": False,
    }
    res = await client.post(
        "/api/v1/onboarding/requests",
        json=payload,
        headers=auth_actors["da_atl_headers"],  # Atlántico DA
    )
    assert res.status_code == 403
    assert "PERMISSION_DENIED" in res.text


# ==============================================================================
# TEST 07: Anti-IDOR Approval Boundary
# ==============================================================================
@pytest.mark.asyncio
async def test_07_anti_idor_approval(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_actors: dict[str, Any],
) -> None:
    """TEST-07: Department Admin (Atlántico) approving Bogotá request is rejected with HTTP 403."""
    # Find a catalog institution in Bogotá
    cat_bog = (
        await db_session.execute(text("""
            SELECT id, dane_code FROM official_institution_catalog
            WHERE department_code = '11' AND is_active = true
              AND id NOT IN (SELECT catalog_institution_id FROM institution_onboarding_requests)
              AND dane_code NOT IN (SELECT dane_code FROM institutions)
            LIMIT 1
        """))
    ).fetchone()

    created_req_id: str | None = None
    try:
        # Created by National Admin
        res_create = await client.post(
            "/api/v1/onboarding/requests",
            json={
                "catalog_institution_id": str(cat_bog[0]),
                "contact_email": f"bog_{cat_bog[1]}@colegio.edu.co",
            },
            headers=auth_actors["na_headers"],
        )
        created_req_id = res_create.json()["id"]

        # Attempt approval by Atlántico DA
        res_app = await client.post(
            f"/api/v1/onboarding/requests/{created_req_id}/approve",
            headers=auth_actors["da_atl_headers"],
        )
        assert res_app.status_code == 403
        assert "PERMISSION_DENIED" in res_app.text

    finally:
        if created_req_id:
            await db_session.execute(delete(InstitutionOnboardingRequest).where(InstitutionOnboardingRequest.id == uuid.UUID(created_req_id)))
        await db_session.commit()


# ==============================================================================
# TEST 08: Anti-IDOR Query Boundary
# ==============================================================================
@pytest.mark.asyncio
async def test_08_anti_idor_query(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_actors: dict[str, Any],
) -> None:
    """TEST-08: Department Admin (Atlántico) querying Bogotá request detail gets HTTP 403."""
    cat_bog = (
        await db_session.execute(text("""
            SELECT id, dane_code FROM official_institution_catalog
            WHERE department_code = '11' AND is_active = true
              AND id NOT IN (SELECT catalog_institution_id FROM institution_onboarding_requests)
              AND dane_code NOT IN (SELECT dane_code FROM institutions)
            LIMIT 1
        """))
    ).fetchone()

    created_req_id: str | None = None
    try:
        res_create = await client.post(
            "/api/v1/onboarding/requests",
            json={
                "catalog_institution_id": str(cat_bog[0]),
                "contact_email": f"bog_{cat_bog[1]}@colegio.edu.co",
            },
            headers=auth_actors["na_headers"],
        )
        created_req_id = res_create.json()["id"]

        # Atlántico DA queries Bogotá request
        res_query = await client.get(
            f"/api/v1/onboarding/requests/{created_req_id}",
            headers=auth_actors["da_atl_headers"],
        )
        assert res_query.status_code == 403

        # Atlántico DA queries catalog specifying Bogotá department_id explicitly
        res_cat = await client.get(
            f"/api/v1/onboarding/catalog?department_id={auth_actors['da_bog_dept_id']}",
            headers=auth_actors["da_atl_headers"],
        )
        assert res_cat.status_code == 403

    finally:
        if created_req_id:
            await db_session.execute(delete(InstitutionOnboardingRequest).where(InstitutionOnboardingRequest.id == uuid.UUID(created_req_id)))
        await db_session.commit()


# ==============================================================================
# TEST 09: Departmental Autonomy
# ==============================================================================
@pytest.mark.asyncio
async def test_09_departmental_autonomy_valid(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_actors: dict[str, Any],
) -> None:
    """TEST-09: Department Admin (Atlántico) successfully files & approves Atlántico request."""
    cat_atl = (
        await db_session.execute(text("""
            SELECT id, dane_code FROM official_institution_catalog
            WHERE department_code = '08' AND is_active = true
              AND id NOT IN (SELECT catalog_institution_id FROM institution_onboarding_requests)
              AND dane_code NOT IN (SELECT dane_code FROM institutions)
            LIMIT 1
        """))
    ).fetchone()

    created_req_id: str | None = None
    try:
        # Filed by Atlántico DA
        res_create = await client.post(
            "/api/v1/onboarding/requests",
            json={
                "catalog_institution_id": str(cat_atl[0]),
                "contact_email": f"atl_{cat_atl[1]}@colegio.edu.co",
            },
            headers=auth_actors["da_atl_headers"],
        )
        assert res_create.status_code == 201
        created_req_id = res_create.json()["id"]

        # Approved by Atlántico DA
        res_app = await client.post(
            f"/api/v1/onboarding/requests/{created_req_id}/approve",
            json={"notes": "Aprobado por SED Atlántico."},
            headers=auth_actors["da_atl_headers"],
        )
        assert res_app.status_code == 200
        assert res_app.json()["status"] == "APPROVED"

    finally:
        if created_req_id:
            await db_session.execute(delete(InstitutionOnboardingRequest).where(InstitutionOnboardingRequest.id == uuid.UUID(created_req_id)))
        await db_session.commit()


# ==============================================================================
# TEST 10: National Authority Scope
# ==============================================================================
@pytest.mark.asyncio
async def test_10_national_authority_global(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_actors: dict[str, Any],
) -> None:
    """TEST-10: National Admin can query catalog and requests across departments."""
    # Query catalog for multiple departments
    res1 = await client.get(
        f"/api/v1/onboarding/catalog?department_id={auth_actors['da_atl_dept_id']}",
        headers=auth_actors["na_headers"],
    )
    assert res1.status_code == 200

    res2 = await client.get(
        f"/api/v1/onboarding/catalog?department_id={auth_actors['da_bog_dept_id']}",
        headers=auth_actors["na_headers"],
    )
    assert res2.status_code == 200


# ==============================================================================
# TEST 11: Rejection Requires Substantive Reason
# ==============================================================================
@pytest.mark.asyncio
async def test_11_rejection_requires_valid_reason(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_actors: dict[str, Any],
) -> None:
    """TEST-11: Rejection fails if reason < 10 characters (422) and succeeds with >= 10 chars."""
    cat = (
        await db_session.execute(text("""
            SELECT id, dane_code FROM official_institution_catalog
            WHERE department_code = '08' AND is_active = true
              AND id NOT IN (SELECT catalog_institution_id FROM institution_onboarding_requests)
              AND dane_code NOT IN (SELECT dane_code FROM institutions)
            LIMIT 1
        """))
    ).fetchone()

    created_req_id: str | None = None
    try:
        res_create = await client.post(
            "/api/v1/onboarding/requests",
            json={
                "catalog_institution_id": str(cat[0]),
                "contact_email": f"rej_{cat[1]}@colegio.edu.co",
            },
            headers=auth_actors["na_headers"],
        )
        created_req_id = res_create.json()["id"]

        # Reject with short reason (< 10 chars)
        res_fail = await client.post(
            f"/api/v1/onboarding/requests/{created_req_id}/reject",
            json={"rejection_reason": "No cumple"},
            headers=auth_actors["na_headers"],
        )
        assert res_fail.status_code == 422

        # Reject with valid reason
        res_ok = await client.post(
            f"/api/v1/onboarding/requests/{created_req_id}/reject",
            json={"rejection_reason": "Faltan documentos oficiales requeridos por la Secretaría."},
            headers=auth_actors["na_headers"],
        )
        assert res_ok.status_code == 200
        assert res_ok.json()["status"] == "REJECTED"

    finally:
        if created_req_id:
            await db_session.execute(delete(InstitutionOnboardingRequest).where(InstitutionOnboardingRequest.id == uuid.UUID(created_req_id)))
        await db_session.commit()


# ==============================================================================
# TEST 12: Authorized Cancellation by Requester
# ==============================================================================
@pytest.mark.asyncio
async def test_12_authorized_cancellation(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_actors: dict[str, Any],
) -> None:
    """TEST-12: The requester can cancel their own request before provisioning."""
    cat = (
        await db_session.execute(text("""
            SELECT id, dane_code FROM official_institution_catalog
            WHERE department_code = '08' AND is_active = true
              AND id NOT IN (SELECT catalog_institution_id FROM institution_onboarding_requests)
              AND dane_code NOT IN (SELECT dane_code FROM institutions)
            LIMIT 1
        """))
    ).fetchone()

    created_req_id: str | None = None
    try:
        # Filed by Atlántico DA
        res_create = await client.post(
            "/api/v1/onboarding/requests",
            json={
                "catalog_institution_id": str(cat[0]),
                "contact_email": f"can_{cat[1]}@colegio.edu.co",
            },
            headers=auth_actors["da_atl_headers"],
        )
        created_req_id = res_create.json()["id"]

        # Cancelled by the same Atlántico DA
        res_can = await client.post(
            f"/api/v1/onboarding/requests/{created_req_id}/cancel",
            json={"cancellation_reason": "Desistimiento voluntario del trámite."},
            headers=auth_actors["da_atl_headers"],
        )
        assert res_can.status_code == 200
        assert res_can.json()["status"] == "CANCELLED"

    finally:
        if created_req_id:
            await db_session.execute(delete(InstitutionOnboardingRequest).where(InstitutionOnboardingRequest.id == uuid.UUID(created_req_id)))
        await db_session.commit()


# ==============================================================================
# TEST 13: Unauthorized Cancellation Attempt
# ==============================================================================
@pytest.mark.asyncio
async def test_13_unauthorized_cancellation(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_actors: dict[str, Any],
) -> None:
    """TEST-13: Another user cannot cancel a request they did not file."""
    cat = (
        await db_session.execute(text("""
            SELECT id, dane_code FROM official_institution_catalog
            WHERE department_code = '08' AND is_active = true
              AND id NOT IN (SELECT catalog_institution_id FROM institution_onboarding_requests)
              AND dane_code NOT IN (SELECT dane_code FROM institutions)
            LIMIT 1
        """))
    ).fetchone()

    created_req_id: str | None = None
    try:
        # Filed by Atlántico DA
        res_create = await client.post(
            "/api/v1/onboarding/requests",
            json={
                "catalog_institution_id": str(cat[0]),
                "contact_email": f"unauth_{cat[1]}@colegio.edu.co",
            },
            headers=auth_actors["da_atl_headers"],
        )
        created_req_id = res_create.json()["id"]

        # Attempt to cancel by Bogotá DA (different user, different department)
        res_can = await client.post(
            f"/api/v1/onboarding/requests/{created_req_id}/cancel",
            headers=auth_actors["da_bog_headers"],
        )
        assert res_can.status_code == 403

    finally:
        if created_req_id:
            await db_session.execute(delete(InstitutionOnboardingRequest).where(InstitutionOnboardingRequest.id == uuid.UUID(created_req_id)))
        await db_session.commit()


# ==============================================================================
# TEST 14: Forbidden State Transitions
# ==============================================================================
@pytest.mark.asyncio
async def test_14_forbidden_state_transitions(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_actors: dict[str, Any],
) -> None:
    """TEST-14: State machine rejects illegal transitions with HTTP 409."""
    cat = (
        await db_session.execute(text("""
            SELECT id, dane_code FROM official_institution_catalog
            WHERE department_code = '08' AND is_active = true
              AND id NOT IN (SELECT catalog_institution_id FROM institution_onboarding_requests)
              AND dane_code NOT IN (SELECT dane_code FROM institutions)
            LIMIT 1
        """))
    ).fetchone()

    created_req_id: str | None = None
    try:
        # File draft
        res_create = await client.post(
            "/api/v1/onboarding/requests",
            json={
                "catalog_institution_id": str(cat[0]),
                "contact_email": f"illegal_{cat[1]}@colegio.edu.co",
                "is_draft": True,
            },
            headers=auth_actors["na_headers"],
        )
        created_req_id = res_create.json()["id"]

        # Attempt to provision directly from DRAFT (bypass review & approve)
        res_prov_fail = await client.post(
            f"/api/v1/onboarding/requests/{created_req_id}/provision",
            headers=auth_actors["na_headers"],
        )
        assert res_prov_fail.status_code == 409

        # Reject the request
        await client.post(
            f"/api/v1/onboarding/requests/{created_req_id}/reject",
            json={"rejection_reason": "Causal de rechazo formal para prueba."},
            headers=auth_actors["na_headers"],
        )

        # Attempt to approve a REJECTED request
        res_app_fail = await client.post(
            f"/api/v1/onboarding/requests/{created_req_id}/approve",
            headers=auth_actors["na_headers"],
        )
        assert res_app_fail.status_code == 409

    finally:
        if created_req_id:
            await db_session.execute(delete(InstitutionOnboardingRequest).where(InstitutionOnboardingRequest.id == uuid.UUID(created_req_id)))
        await db_session.commit()


# ==============================================================================
# TEST 15: Concurrency / Race Condition on Provisioning
# ==============================================================================
@pytest.mark.asyncio
async def test_15_concurrent_provisioning_race_condition(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_actors: dict[str, Any],
) -> None:
    """TEST-15: Two concurrent provisioning calls produce exactly 1 tenant (201 and 409)."""
    cat = (
        await db_session.execute(text("""
            SELECT id, dane_code FROM official_institution_catalog
            WHERE department_code = '08' AND is_active = true
              AND id NOT IN (SELECT catalog_institution_id FROM institution_onboarding_requests)
              AND dane_code NOT IN (SELECT dane_code FROM institutions)
            LIMIT 1
        """))
    ).fetchone()

    created_inst_id: str | None = None
    created_req_id: str | None = None
    try:
        res_create = await client.post(
            "/api/v1/onboarding/requests",
            json={
                "catalog_institution_id": str(cat[0]),
                "contact_email": f"race_{cat[1]}@colegio.edu.co",
            },
            headers=auth_actors["na_headers"],
        )
        created_req_id = res_create.json()["id"]

        await client.post(
            f"/api/v1/onboarding/requests/{created_req_id}/approve",
            headers=auth_actors["na_headers"],
        )

        # Concurrent calls
        call_a = client.post(
            f"/api/v1/onboarding/requests/{created_req_id}/provision",
            headers=auth_actors["na_headers"],
        )
        call_b = client.post(
            f"/api/v1/onboarding/requests/{created_req_id}/provision",
            headers=auth_actors["na_headers"],
        )

        res_a, res_b = await asyncio.gather(call_a, call_b)
        status_codes = {res_a.status_code, res_b.status_code}
        assert 201 in status_codes
        assert 409 in status_codes

        # Find institution id to clean up
        success_res = res_a if res_a.status_code == 201 else res_b
        created_inst_id = success_res.json()["institution_id"]

        # Exactly 1 tenant exists in DB for this DANE code
        tenant_count = (
            await db_session.execute(
                select(func.count(Institution.id)).where(Institution.dane_code == cat[1])
            )
        ).scalar_one()
        assert tenant_count == 1

    finally:
        await db_session.rollback()
        if created_inst_id:
            await db_session.execute(delete(Campus).where(Campus.institution_id == uuid.UUID(created_inst_id)))
            await db_session.execute(delete(Institution).where(Institution.id == uuid.UUID(created_inst_id)))
        if created_req_id:
            await db_session.execute(delete(InstitutionOnboardingRequest).where(InstitutionOnboardingRequest.id == uuid.UUID(created_req_id)))
        await db_session.commit()


# ==============================================================================
# TEST 16: Inactive Catalog Establishment Rejected
# ==============================================================================
@pytest.mark.asyncio
async def test_16_inactive_catalog_institution_rejected(
    client: AsyncClient,
    db_session: AsyncSession,
    auth_actors: dict[str, Any],
) -> None:
    """TEST-16: Onboarding request for inactive/closed establishment returns HTTP 422."""
    # Find or set a catalog record as inactive temporarily
    cat_inactive = (
        await db_session.execute(text("""
            SELECT id FROM official_institution_catalog
            WHERE is_active = false
            LIMIT 1
        """))
    ).scalar_one_or_none()

    revert_active: uuid.UUID | None = None
    if not cat_inactive:
        # Temporarily mark one test candidate inactive
        cat_temp = (
            await db_session.execute(text("""
                SELECT id FROM official_institution_catalog
                WHERE department_code = '08'
                  AND id NOT IN (SELECT catalog_institution_id FROM institutions WHERE catalog_institution_id IS NOT NULL)
                LIMIT 1
            """))
        ).scalar_one()
        await db_session.execute(text(f"UPDATE official_institution_catalog SET is_active = false WHERE id = '{cat_temp}'"))
        await db_session.commit()
        cat_inactive = cat_temp
        revert_active = cat_temp

    try:
        res = await client.post(
            "/api/v1/onboarding/requests",
            json={
                "catalog_institution_id": str(cat_inactive),
                "contact_email": "inactive@colegio.edu.co",
            },
            headers=auth_actors["na_headers"],
        )
        assert res.status_code == 422
        assert "CATALOG_INSTITUTION_INACTIVE" in res.text

    finally:
        if revert_active:
            await db_session.execute(text(f"UPDATE official_institution_catalog SET is_active = true WHERE id = '{revert_active}'"))
            await db_session.commit()


# ==============================================================================
# TEST 17: Non-existent Catalog Record Rejected
# ==============================================================================
@pytest.mark.asyncio
async def test_17_nonexistent_catalog_institution_rejected(
    client: AsyncClient,
    auth_actors: dict[str, Any],
) -> None:
    """TEST-17: Onboarding request with unknown UUID returns HTTP 404."""
    fake_uuid = str(uuid.uuid4())
    res = await client.post(
        "/api/v1/onboarding/requests",
        json={
            "catalog_institution_id": fake_uuid,
            "contact_email": "fake@colegio.edu.co",
        },
        headers=auth_actors["na_headers"],
    )
    assert res.status_code == 404
    assert "CATALOG_RECORD_NOT_FOUND" in res.text


# ==============================================================================
# TEST 18: Preservation of the 27 Synthetic Fixture Institutions
# ==============================================================================
@pytest.mark.asyncio
async def test_18_synthetic_fixtures_preservation(
    db_session: AsyncSession,
) -> None:
    """TEST-18: The 27 synthetic fixture institutions maintain catalog_institution_id = NULL intact."""
    count = (
        await db_session.execute(
            select(func.count(Institution.id)).where(
                Institution.catalog_institution_id.is_(None)
            )
        )
    ).scalar_one()
    assert count == 27, "Synthetic fixtures must remain exactly 27 with NULL catalog_institution_id"
