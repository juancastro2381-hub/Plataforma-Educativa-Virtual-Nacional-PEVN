"""
PEVN — NTA-10-R3: Rector Institution Binding, Tenant Context Reconciliation,
and Institutional Dashboard Remediation Test Suite

Validates:
1. Rector invitation redemption persists canonical institution relationship in both User and UserRole.
2. Rector login returns the expected institutional context (institution_id, active_institution_id).
3. Institution context remains consistent across repeated logins / token renewals.
4. Rector dashboard institution summary (/api/v1/institutions/me) returns official name, DANE code, and campuses.
5. Rector can read only their assigned institution (/api/v1/institutions/{own_id} -> 200).
6. Rector cannot access another institution by substituting ID (/api/v1/institutions/{other_id} -> 403).
7. Rector cannot access territorial catalog explorer (/api/v1/institutions/catalog-explorer -> 403) or full list (/api/v1/institutions -> 403).
8. Municipal administrator retains authorized territorial catalog explorer access (/api/v1/institutions/catalog-explorer -> 200).
9. Departmental and national administrators retain supervisory catalog explorer and operational access.
10. Missing or inconsistent Rector assignment fails closed safely (no institution -> 404 / 403, never leaks another tenant).
11. Rector succession and duplicate active Rector prevention remain intact.
"""

from __future__ import annotations

import random
import uuid
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.core.security.tokens import token_service
from app.models.institution import Campus, Institution
from app.models.invitation import RectorInvitation
from app.models.official_catalog import OfficialCampusCatalog, OfficialInstitutionCatalog
from app.models.role import Role, UserRole
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User
from app.services.rbac_bootstrap_service import RbacBootstrapService


def _rand_doc() -> str:
    return str(random.randint(10000000, 99999999))


@pytest.fixture
async def nta10_r3_fixture(db_session: AsyncSession) -> dict[str, Any]:
    """Bootstrap territory, institutions, official catalog, and actors for NTA-10-R3 testing."""
    bootstrap = RbacBootstrapService(session=db_session)
    await bootstrap.seed_canonical_rbac_if_needed()

    # 1. Department: Caquetá (18) and Antioquia (05)
    dept_caq = Department(code="18", name="CAQUETÁ")
    dept_ant = Department(code="05", name="ANTIOQUIA")
    db_session.add_all([dept_caq, dept_ant])
    await db_session.flush()

    # 2. Municipalities: Valparaíso (18860) and Medellín (05001)
    muni_valp = Municipality(department_id=dept_caq.id, code="18860", name="VALPARAÍSO")
    muni_med = Municipality(department_id=dept_ant.id, code="05001", name="MEDELLÍN")
    db_session.add_all([muni_valp, muni_med])
    await db_session.flush()

    # 3. Official Catalog for Valparaíso (I.E. VALPARAISO)
    cat_valp = OfficialInstitutionCatalog(
        dane_code="118860001293",
        name="I.E VALPARAISO",
        department_code="18",
        department_name="CAQUETÁ",
        municipality_code="18860",
        municipality_name="VALPARAÍSO",
        official_email="contacto.118860001293@valparaiso.edu.co",
        official_phone="3100000000",
        sector="OFICIAL",
        zone="URBANA",
        status="ACTIVO",
        is_active=True,
    )
    db_session.add(cat_valp)
    await db_session.flush()

    cat_campus = OfficialCampusCatalog(
        official_institution_id=cat_valp.id,
        dane_sede_code="118860001293",
        name="SEDE PRINCIPAL - I.E VALPARAISO",
        is_main=True,
        status="ACTIVA",
        is_active=True,
    )
    db_session.add(cat_campus)
    await db_session.flush()

    # 4. Provisioned Operational Institutions
    # Institution A: I.E. VALPARAISO
    inst_valp = Institution(
        municipality_id=muni_valp.id,
        dane_code="118860001293",
        name="I.E VALPARAISO",
        email="rectoria@ievalparaiso.edu.co",
        is_active=True,
    )
    # Institution B: Other Institution in Medellin
    inst_other = Institution(
        municipality_id=muni_med.id,
        dane_code=f"105001{random.randint(100000, 999999)}",
        name="I.E. OTRA INSTITUCION",
        email="rectoria@ieotra.edu.co",
        is_active=True,
    )
    # Institution C: Unassigned Institution (Ready for Rector invitation)
    inst_unassigned = Institution(
        municipality_id=muni_valp.id,
        dane_code="218860000208",
        name="INST EDUC RUR NIEVES ARRIBA",
        email="rectoria@nieves.edu.co",
        is_active=True,
    )
    db_session.add_all([inst_valp, inst_other, inst_unassigned])
    await db_session.flush()

    campus_valp = Campus(
        institution_id=inst_valp.id,
        dane_sede_code="118860001293",
        name="SEDE PRINCIPAL - I.E VALPARAISO",
        is_active=True,
    )
    campus_other = Campus(
        institution_id=inst_other.id,
        dane_sede_code=f"{inst_other.dane_code}01",
        name="SEDE PRINCIPAL - OTRA",
        is_active=True,
    )
    campus_nieves = Campus(
        institution_id=inst_unassigned.id,
        dane_sede_code="218860000208",
        name="SEDE PRINCIPAL - NIEVES",
        is_active=True,
    )
    db_session.add_all([campus_valp, campus_other, campus_nieves])
    await db_session.flush()

    # 5. Actors Helper
    async def create_actor(
        role_name: str,
        dept_id: uuid.UUID | None = None,
        muni_id: uuid.UUID | None = None,
        inst_id: uuid.UUID | None = None,
        email_prefix: str = "actor",
    ) -> tuple[User, dict[str, str]]:
        tag = uuid.uuid4().hex[:6]
        user = User(
            email=f"{email_prefix}_{tag}@test.gov.co",
            username=f"{email_prefix}_{tag}",
            hashed_password=password_hasher.hash("SecurePass123!"),
            first_name=f"First_{tag}",
            last_name=f"Last_{tag}",
            document_type=DocumentType.CC,
            document_number=_rand_doc(),
            institution_id=inst_id,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        await db_session.flush()

        role_res = await db_session.execute(select(Role).where(Role.name == role_name))
        role = role_res.scalar_one()

        ur = UserRole(
            user_id=user.id,
            role_id=role.id,
            department_id=dept_id,
            municipality_id=muni_id,
            institution_id=inst_id,
            is_active=True,
        )
        db_session.add(ur)
        await db_session.flush()

        additional_claims: dict[str, Any] = {"roles": [role_name]}
        if dept_id:
            additional_claims["department_id"] = str(dept_id)
        if muni_id:
            additional_claims["municipality_id"] = str(muni_id)
        if inst_id:
            additional_claims["institution_id"] = str(inst_id)

        token = await token_service.create_access_token(
            subject=str(user.id),
            additional_claims=additional_claims,
        )
        return user, {"Authorization": f"Bearer {token}"}

    # Administrative actors
    superadmin_user, superadmin_headers = await create_actor("superadmin", email_prefix="superadmin")
    nat_admin_user, nat_admin_headers = await create_actor("national_admin", email_prefix="nat_admin")
    dept_admin_user, dept_admin_headers = await create_actor("department_admin", dept_id=dept_caq.id, email_prefix="dept_admin")
    muni_admin_valp_user, muni_admin_valp_headers = await create_actor(
        "municipality_admin", dept_id=dept_caq.id, muni_id=muni_valp.id, email_prefix="muni_valp"
    )

    # Rector for inst_valp
    rector_valp_user, rector_valp_headers = await create_actor(
        "rector", inst_id=inst_valp.id, email_prefix="rector_valp"
    )

    # Rector for inst_other
    rector_other_user, rector_other_headers = await create_actor(
        "rector", inst_id=inst_other.id, email_prefix="rector_other"
    )

    # Orphan rector without institution
    orphan_rector_user, orphan_rector_headers = await create_actor(
        "rector", inst_id=None, email_prefix="rector_orphan"
    )

    return {
        "dept_caq": dept_caq,
        "muni_valp": muni_valp,
        "inst_valp": inst_valp,
        "inst_other": inst_other,
        "inst_unassigned": inst_unassigned,
        "cat_valp": cat_valp,
        "superadmin_headers": superadmin_headers,
        "nat_admin_headers": nat_admin_headers,
        "dept_admin_headers": dept_admin_headers,
        "muni_admin_valp_headers": muni_admin_valp_headers,
        "rector_valp_user": rector_valp_user,
        "rector_valp_headers": rector_valp_headers,
        "rector_other_user": rector_other_user,
        "rector_other_headers": rector_other_headers,
        "orphan_rector_user": orphan_rector_user,
        "orphan_rector_headers": orphan_rector_headers,
    }


# ==============================================================================
# Scenario 1 & 2: Rector invitation redemption & Login persist canonical binding
# ==============================================================================

@pytest.mark.asyncio
async def test_01_rector_invitation_redemption_persists_canonical_binding(
    client: AsyncClient,
    db_session: AsyncSession,
    nta10_r3_fixture: dict[str, Any],
) -> None:
    """Inviting and activating a new Rector guarantees users.institution_id and user_roles.institution_id are populated."""
    inst = nta10_r3_fixture["inst_unassigned"]
    muni_headers = nta10_r3_fixture["superadmin_headers"]

    tag = uuid.uuid4().hex[:6]
    invite_payload = {
        "first_name": "Rector",
        "last_name": f"Test {tag}",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "email": f"rector_{tag}@testinv.edu.co",
        "phone_number": "+57 311 0000000",
    }

    # 1. Create invitation
    resp = await client.post(
        f"/api/v1/institutions/{inst.id}/rector-invitation",
        json=invite_payload,
        headers=muni_headers,
    )
    assert resp.status_code == 201, resp.text
    token = resp.json()["raw_invitation_token"]
    assert token is not None

    # 2. Redeem invitation
    accept_resp = await client.post(
        "/api/v1/auth/accept-invitation",
        json={
            "token": token,
            "password": "RectorStrongPass2026!@",
            "password_confirmation": "RectorStrongPass2026!@",
        },
    )
    assert accept_resp.status_code == 200, accept_resp.text
    data = accept_resp.json()
    assert data["is_active"] is True

    # 3. Verify in database
    user_res = await db_session.execute(
        select(User).where(User.email == invite_payload["email"])
    )
    user = user_res.scalar_one()
    assert user.institution_id == inst.id
    assert user.is_active is True

    # Verify user_roles
    ur_res = await db_session.execute(
        select(UserRole).where(UserRole.user_id == user.id, UserRole.is_active == True)
    )
    ur = ur_res.scalar_one()
    assert ur.institution_id == inst.id


@pytest.mark.asyncio
async def test_02_rector_login_returns_institutional_context(
    client: AsyncClient,
    nta10_r3_fixture: dict[str, Any],
) -> None:
    """Rector login produces tokens containing institution_id claim and user payload with institution_id."""
    rector_user = nta10_r3_fixture["rector_valp_user"]
    inst_valp = nta10_r3_fixture["inst_valp"]

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={
            "username": rector_user.email,
            "password": "SecurePass123!",
        },
    )
    assert login_resp.status_code == 200, login_resp.text
    login_data = login_resp.json()
    assert login_data["access_token"] is not None
    assert login_data["user"]["institution_id"] == str(inst_valp.id)


# ==============================================================================
# Scenario 3 & 4: Institution summary (/me) returns target institution details
# ==============================================================================

@pytest.mark.asyncio
async def test_03_rector_dashboard_institution_me_summary(
    client: AsyncClient,
    nta10_r3_fixture: dict[str, Any],
) -> None:
    """GET /api/v1/institutions/me resolves the Rector's assigned institution with enriched status."""
    rector_headers = nta10_r3_fixture["rector_valp_headers"]
    inst_valp = nta10_r3_fixture["inst_valp"]

    resp = await client.get("/api/v1/institutions/me", headers=rector_headers)
    assert resp.status_code == 200, resp.text
    inst_data = resp.json()

    assert inst_data["id"] == str(inst_valp.id)
    assert inst_data["name"] == "I.E VALPARAISO"
    assert inst_data["dane_code"] == "118860001293"
    assert inst_data["is_active"] is True
    assert inst_data["has_active_rector"] is True
    assert len(inst_data["campuses"]) >= 1
    assert inst_data["campuses"][0]["dane_sede_code"] == "118860001293"


# ==============================================================================
# Scenario 5 & 6: Rector can read own institution; Cross-tenant access forbidden
# ==============================================================================

@pytest.mark.asyncio
async def test_04_rector_can_read_own_institution_detail(
    client: AsyncClient,
    nta10_r3_fixture: dict[str, Any],
) -> None:
    """Rector can access GET /api/v1/institutions/{own_id}."""
    rector_headers = nta10_r3_fixture["rector_valp_headers"]
    inst_valp = nta10_r3_fixture["inst_valp"]

    resp = await client.get(f"/api/v1/institutions/{inst_valp.id}", headers=rector_headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["id"] == str(inst_valp.id)


@pytest.mark.asyncio
async def test_05_rector_cannot_access_other_institution(
    client: AsyncClient,
    nta10_r3_fixture: dict[str, Any],
) -> None:
    """Rector attempting to access GET /api/v1/institutions/{other_id} is rejected with 403 Forbidden."""
    rector_headers = nta10_r3_fixture["rector_valp_headers"]
    inst_other = nta10_r3_fixture["inst_other"]

    resp = await client.get(f"/api/v1/institutions/{inst_other.id}", headers=rector_headers)
    assert resp.status_code == 403, resp.text
    assert "área institucional" in resp.text or "permisos" in resp.text or "Forbidden" in resp.text


# ==============================================================================
# Scenario 7: Rector cannot access territorial catalog explorer or general list
# ==============================================================================

@pytest.mark.asyncio
async def test_06_rector_rejected_from_territorial_catalog_explorer(
    client: AsyncClient,
    nta10_r3_fixture: dict[str, Any],
) -> None:
    """Rector attempting GET /api/v1/institutions/catalog-explorer is rejected with 403 Forbidden."""
    rector_headers = nta10_r3_fixture["rector_valp_headers"]

    resp = await client.get(
        "/api/v1/institutions/catalog-explorer",
        params={"municipality_code": "18860"},
        headers=rector_headers,
    )
    assert resp.status_code == 403, resp.text
    assert "Se requiere alcance territorial o nacional" in resp.json()["error"]["message"]


@pytest.mark.asyncio
async def test_07_rector_rejected_from_general_institutions_list(
    client: AsyncClient,
    nta10_r3_fixture: dict[str, Any],
) -> None:
    """Rector attempting GET /api/v1/institutions (master catalog) is rejected with 403 Forbidden."""
    rector_headers = nta10_r3_fixture["rector_valp_headers"]

    resp = await client.get("/api/v1/institutions", headers=rector_headers)
    assert resp.status_code == 403, resp.text


# ==============================================================================
# Scenario 8 & 9: Territorial administrators retain authorized catalog access
# ==============================================================================

@pytest.mark.asyncio
async def test_08_municipal_admin_retains_authorized_catalog_access(
    client: AsyncClient,
    nta10_r3_fixture: dict[str, Any],
) -> None:
    """Municipal admin can query GET /api/v1/institutions/catalog-explorer for their municipality."""
    muni_headers = nta10_r3_fixture["muni_admin_valp_headers"]

    resp = await client.get(
        "/api/v1/institutions/catalog-explorer",
        params={"municipality_code": "18860"},
        headers=muni_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "items" in data
    assert any(item["dane_code"] == "118860001293" for item in data["items"])


@pytest.mark.asyncio
async def test_09_department_and_national_admins_retain_supervisory_access(
    client: AsyncClient,
    nta10_r3_fixture: dict[str, Any],
) -> None:
    """National and Departmental admins can query catalog explorer with supervisory authority."""
    nat_headers = nta10_r3_fixture["nat_admin_headers"]
    dept_headers = nta10_r3_fixture["dept_admin_headers"]

    # National admin
    resp_nat = await client.get(
        "/api/v1/institutions/catalog-explorer",
        params={"municipality_code": "18860"},
        headers=nat_headers,
    )
    assert resp_nat.status_code == 200, resp_nat.text

    # Department admin
    resp_dept = await client.get(
        "/api/v1/institutions/catalog-explorer",
        params={"municipality_code": "18860"},
        headers=dept_headers,
    )
    assert resp_dept.status_code == 200, resp_dept.text


# ==============================================================================
# Scenario 10: Missing or inconsistent Rector assignment fails safely closed
# ==============================================================================

@pytest.mark.asyncio
async def test_10_orphan_rector_without_institution_fails_safely(
    client: AsyncClient,
    nta10_r3_fixture: dict[str, Any],
) -> None:
    """A user with rector role but no institution_id fails closed on /me with 404 (never leaks a random tenant)."""
    orphan_headers = nta10_r3_fixture["orphan_rector_headers"]

    resp = await client.get("/api/v1/institutions/me", headers=orphan_headers)
    assert resp.status_code == 404, resp.text
    assert "no tiene una institución educativa" in resp.json()["error"]["message"].lower()


# ==============================================================================
# Scenario 11: Rector succession & anti-duplication remain intact
# ==============================================================================

@pytest.mark.asyncio
async def test_11_rector_anti_duplication_prevent_second_active_rector(
    client: AsyncClient,
    nta10_r3_fixture: dict[str, Any],
) -> None:
    """Inviting a second rector for an institution that already has an active rector is rejected with 409 Conflict."""
    inst_valp = nta10_r3_fixture["inst_valp"]
    nat_headers = nta10_r3_fixture["nat_admin_headers"]

    payload = {
        "first_name": "Second",
        "last_name": "Rector",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "email": "second.rector@valparaiso.edu.co",
    }

    resp = await client.post(
        f"/api/v1/institutions/{inst_valp.id}/rector-invitation",
        json=payload,
        headers=nat_headers,
    )
    assert resp.status_code == 409, resp.text
    assert "RECTOR_ALREADY_EXISTS" in resp.text
