"""
PEVN Backend — NTA-08 Canonical Authority Chain & Role Provisioning Test Suite
AI Software Factory Standard v1.2

Mandatory Test Coverage for Canonical Authority Hierarchy:
  SUPERADMIN (100)
      │
      ▼
  NATIONAL_ADMIN (90)
      │
      ▼
  DEPARTMENT_ADMIN (80)
      │
      ▼
  MUNICIPALITY_ADMIN (70)
      │
      ▼
  RECTOR / DIRECTOR (60)
      │
      ▼
  COORDINATOR (50)
      │
      ├──────────────┐
      ▼              ▼
  TEACHER (30)   STUDENT (10)
                     │
                     ▼
                  GUARDIAN (10)

Tests:
  1. SUPERADMIN authority (global, can provision across territorial boundaries)
  2. NATIONAL_ADMIN authority (national, can provision departmental & municipal roles)
  3. DEPARTMENT_ADMIN -> MUNICIPALITY_ADMIN (can provision only within own department)
  4. DEPARTMENT_ADMIN -> RECTOR (can invite rector within own department; foreign dept 403)
  5. MUNICIPALITY_ADMIN -> RECTOR (can invite rector within own municipality; foreign muni 403)
  6. RECTOR -> COORDINATOR (can provision coordinator within own institution)
  7. RECTOR -> TEACHER (can provision teacher within own institution)
  8. RECTOR -> STUDENT (can provision student within own institution)
  9. COORDINATOR -> TEACHER (can provision teacher within own institution)
  10. COORDINATOR -> STUDENT (can provision student within own institution)
  11. GUARDIAN workflow (institutional context preserved, student-guardian linking)
  12. Cross-department rejection (Anti-IDOR: 403)
  13. Cross-municipality rejection (Anti-IDOR: 403)
  14. Cross-institution rejection (Anti-IDOR: 403)
  15. Role escalation rejection (Lower roles cannot assign higher roles or mutate roles)
  16. Scope tampering rejection (Client-supplied IDs do not bypass server authorization)
  17. Rector succession (Atomic one-active-rector enforcement via revocation & succession)
  18. Invitation replay rejection (Single-use token enforcement)
  19. Invitation expiration (Expired token rejected)
  20. Session invalidation after revocation/reassignment (Tokens marked revoked)
"""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.interfaces import AuditEventType
from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.core.security.tokens import hash_token, token_service
from app.models.audit_log import AuditLog
from app.models.institution import Institution
from app.models.invitation import RectorInvitation
from app.models.role import Role, UserRole
from app.models.territory import Department, Municipality
from app.models.token import RefreshToken
from app.models.user import DocumentType, User
from app.services.rbac_bootstrap_service import RbacBootstrapService


def _rand_doc() -> str:
    return str(secrets.randbelow(899999999) + 100000000)


@pytest.fixture
async def nta08_fixture(db_session: AsyncSession) -> dict[str, Any]:
    """Bootstrap canonical RBAC and territorial test entities."""
    # Ensure canonical roles & permissions are in DB
    bootstrap = RbacBootstrapService(session=db_session)
    await bootstrap.seed_canonical_rbac_if_needed()

    # 1. Departments: Atlántico (08) and Cundinamarca (25)
    dept_atl = Department(code=f"08_{uuid.uuid4().hex[:4]}", name="Atlántico Test")
    dept_cun = Department(code=f"25_{uuid.uuid4().hex[:4]}", name="Cundinamarca Test")
    db_session.add_all([dept_atl, dept_cun])
    await db_session.flush()

    # 2. Municipalities
    muni_barranquilla = Municipality(
        department_id=dept_atl.id,
        code=f"08001_{uuid.uuid4().hex[:4]}",
        name="Barranquilla Test",
    )
    muni_soledad = Municipality(
        department_id=dept_atl.id,
        code=f"08758_{uuid.uuid4().hex[:4]}",
        name="Soledad Test",
    )
    muni_facatativa = Municipality(
        department_id=dept_cun.id,
        code=f"25269_{uuid.uuid4().hex[:4]}",
        name="Facatativá Test",
    )
    db_session.add_all([muni_barranquilla, muni_soledad, muni_facatativa])
    await db_session.flush()

    # 3. Institutions
    inst_baq = Institution(
        municipality_id=muni_barranquilla.id,
        dane_code=f"108001{secrets.randbelow(900000) + 100000}",
        name="Colegio Barranquilla NTA08",
        email=f"inst_baq_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        is_active=True,
    )
    inst_faca = Institution(
        municipality_id=muni_facatativa.id,
        dane_code=f"125269{secrets.randbelow(900000) + 100000}",
        name="Colegio Facatativa NTA08",
        email=f"inst_faca_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        is_active=True,
    )
    # Vacant institutions without active rectors (for invitation tests)
    inst_baq_vacant = Institution(
        municipality_id=muni_barranquilla.id,
        dane_code=f"108001{secrets.randbelow(900000) + 100000}",
        name="Colegio Barranquilla Vacant NTA08",
        email=f"inst_baq_vac_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        is_active=True,
    )
    inst_faca_vacant = Institution(
        municipality_id=muni_facatativa.id,
        dane_code=f"125269{secrets.randbelow(900000) + 100000}",
        name="Colegio Facatativa Vacant NTA08",
        email=f"inst_faca_vac_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        is_active=True,
    )
    db_session.add_all([inst_baq, inst_faca, inst_baq_vacant, inst_faca_vacant])
    await db_session.flush()

    # Helper function to create authenticated user
    async def create_actor(role_name: str, *, dept_id=None, muni_id=None, inst_id=None) -> tuple[User, str, dict[str, str]]:
        role_obj = (await db_session.execute(select(Role).where(Role.name == role_name))).scalar_one()
        pw = password_hasher.hash("TestPass2026!#")
        uid = uuid.uuid4()
        user = User(
            id=uid,
            email=f"{role_name}_{uid.hex[:6]}@pevn.edu.co",
            username=f"{role_name}_{uid.hex[:6]}",
            hashed_password=pw,
            first_name=role_name.capitalize(),
            last_name="Actor",
            document_type=DocumentType.CC,
            document_number=_rand_doc(),
            institution_id=inst_id,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        await db_session.flush()

        ur = UserRole(
            user_id=user.id,
            role_id=role_obj.id,
            department_id=dept_id,
            municipality_id=muni_id,
            institution_id=inst_id,
            is_active=True,
        )
        db_session.add(ur)
        await db_session.flush()

        token = await token_service.create_access_token(
            subject=str(user.id),
            additional_claims={
                "roles": [role_name],
                "institution_id": str(inst_id) if inst_id else None,
            },
        )
        headers = {"Authorization": f"Bearer {token}"}
        return user, token, headers

    # Create key actors across hierarchy
    superadmin_user, superadmin_token, superadmin_headers = await create_actor("superadmin")
    nat_admin_user, nat_admin_token, nat_admin_headers = await create_actor("national_admin")
    dept_admin_user, dept_admin_token, dept_admin_headers = await create_actor(
        "department_admin", dept_id=dept_atl.id
    )
    muni_admin_user, muni_admin_token, muni_admin_headers = await create_actor(
        "municipality_admin", dept_id=dept_atl.id, muni_id=muni_barranquilla.id
    )
    rector_user, rector_token, rector_headers = await create_actor(
        "rector", inst_id=inst_baq.id
    )
    coord_user, coord_token, coord_headers = await create_actor(
        "coordinator", inst_id=inst_baq.id
    )
    teacher_user, teacher_token, teacher_headers = await create_actor(
        "teacher", inst_id=inst_baq.id
    )
    student_user, student_token, student_headers = await create_actor(
        "student", inst_id=inst_baq.id
    )

    await db_session.commit()

    return {
        "dept_atl": dept_atl,
        "dept_cun": dept_cun,
        "muni_barranquilla": muni_barranquilla,
        "muni_soledad": muni_soledad,
        "muni_facatativa": muni_facatativa,
        "inst_baq": inst_baq,
        "inst_faca": inst_faca,
        "inst_baq_vacant": inst_baq_vacant,
        "inst_faca_vacant": inst_faca_vacant,
        "superadmin_headers": superadmin_headers,
        "nat_admin_headers": nat_admin_headers,
        "dept_admin_headers": dept_admin_headers,
        "muni_admin_headers": muni_admin_headers,
        "rector_headers": rector_headers,
        "coord_headers": coord_headers,
        "teacher_headers": teacher_headers,
        "student_headers": student_headers,
        "superadmin_user": superadmin_user,
        "dept_admin_user": dept_admin_user,
        "muni_admin_user": muni_admin_user,
        "rector_user": rector_user,
        "coord_user": coord_user,
        "create_actor": create_actor,
    }


# ==============================================================================
# 1. SUPERADMIN AUTHORITY
# ==============================================================================
@pytest.mark.asyncio
async def test_01_superadmin_authority(client: AsyncClient, nta08_fixture: dict[str, Any]):
    headers = nta08_fixture["superadmin_headers"]
    muni_faca = nta08_fixture["muni_facatativa"]

    # Superadmin can provision Municipality Admin in any department/municipality
    payload = {
        "municipality_id": str(muni_faca.id),
        "email": f"super_prov_muni_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "username": f"super_prov_muni_{uuid.uuid4().hex[:6]}",
        "first_name": "Super",
        "last_name": "Provisioned",
        "document_type": "CC",
        "document_number": _rand_doc(),
    }
    res = await client.post("/api/v1/municipality-admins", json=payload, headers=headers)
    assert res.status_code == 201
    assert res.json()["municipality_id"] == str(muni_faca.id)


# ==============================================================================
# 2. NATIONAL_ADMIN AUTHORITY
# ==============================================================================
@pytest.mark.asyncio
async def test_02_national_admin_authority(client: AsyncClient, nta08_fixture: dict[str, Any]):
    headers = nta08_fixture["nat_admin_headers"]
    muni_baq = nta08_fixture["muni_barranquilla"]

    # National Admin can provision Municipality Admin
    payload = {
        "municipality_id": str(muni_baq.id),
        "email": f"nat_prov_muni_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "username": f"nat_prov_muni_{uuid.uuid4().hex[:6]}",
        "first_name": "Nat",
        "last_name": "Provisioned",
        "document_type": "CC",
        "document_number": _rand_doc(),
    }
    res = await client.post("/api/v1/municipality-admins", json=payload, headers=headers)
    assert res.status_code == 201
    assert res.json()["municipality_id"] == str(muni_baq.id)


# ==============================================================================
# 3. DEPARTMENT_ADMIN -> MUNICIPALITY_ADMIN
# ==============================================================================
@pytest.mark.asyncio
async def test_03_dept_admin_provisions_muni_admin_in_own_department(
    client: AsyncClient, nta08_fixture: dict[str, Any]
):
    headers = nta08_fixture["dept_admin_headers"]  # Scoped to Atlántico
    muni_soledad = nta08_fixture["muni_soledad"]  # In Atlántico
    muni_faca = nta08_fixture["muni_facatativa"]  # In Cundinamarca

    # 1. Allowed inside own department
    payload_valid = {
        "municipality_id": str(muni_soledad.id),
        "email": f"dept_prov_soledad_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "username": f"dept_prov_soledad_{uuid.uuid4().hex[:6]}",
        "first_name": "Soledad",
        "last_name": "Admin",
        "document_type": "CC",
        "document_number": _rand_doc(),
    }
    res_valid = await client.post("/api/v1/municipality-admins", json=payload_valid, headers=headers)
    assert res_valid.status_code == 201
    assert res_valid.json()["department_id"] == str(nta08_fixture["dept_atl"].id)

    # 2. Blocked outside department (Cundinamarca) -> 403
    payload_invalid = {
        "municipality_id": str(muni_faca.id),
        "email": f"dept_prov_faca_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "username": f"dept_prov_faca_{uuid.uuid4().hex[:6]}",
        "first_name": "Foreign",
        "last_name": "Admin",
        "document_type": "CC",
        "document_number": _rand_doc(),
    }
    res_invalid = await client.post("/api/v1/municipality-admins", json=payload_invalid, headers=headers)
    assert res_invalid.status_code == 403


# ==============================================================================
# 4. DEPARTMENT_ADMIN -> RECTOR
# ==============================================================================
@pytest.mark.asyncio
async def test_04_dept_admin_invites_rector(
    client: AsyncClient, nta08_fixture: dict[str, Any]
):
    headers = nta08_fixture["dept_admin_headers"]  # Atlántico
    inst_baq_vacant = nta08_fixture["inst_baq_vacant"]  # Atlántico (vacant)
    inst_faca_vacant = nta08_fixture["inst_faca_vacant"]  # Cundinamarca (vacant)

    # 1. Allowed for institution in own department
    payload = {
        "first_name": "Carlos",
        "last_name": "Valderrama",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "email": f"rector_baq_{uuid.uuid4().hex[:6]}@pevn.edu.co",
    }
    res = await client.post(
        f"/api/v1/institutions/{inst_baq_vacant.id}/rector-invitation",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 201
    assert "raw_invitation_token" in res.json()

    # 2. Blocked for institution in other department -> 403
    res_other = await client.post(
        f"/api/v1/institutions/{inst_faca_vacant.id}/rector-invitation",
        json=payload,
        headers=headers,
    )
    assert res_other.status_code == 403


# ==============================================================================
# 5. MUNICIPALITY_ADMIN -> RECTOR
# ==============================================================================
@pytest.mark.asyncio
async def test_05_muni_admin_invites_rector(
    client: AsyncClient, nta08_fixture: dict[str, Any]
):
    headers = nta08_fixture["muni_admin_headers"]  # Barranquilla
    inst_baq_vacant = nta08_fixture["inst_baq_vacant"]  # Barranquilla
    inst_faca_vacant = nta08_fixture["inst_faca_vacant"]  # Facatativá

    # 1. Allowed for institution in own municipality
    payload = {
        "first_name": "Edgar",
        "last_name": "Renteria",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "email": f"rector_renteria_{uuid.uuid4().hex[:6]}@pevn.edu.co",
    }
    res = await client.post(
        f"/api/v1/institutions/{inst_baq_vacant.id}/rector-invitation",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 201

    # 2. Blocked for institution in other municipality -> 403
    res_other = await client.post(
        f"/api/v1/institutions/{inst_faca_vacant.id}/rector-invitation",
        json=payload,
        headers=headers,
    )
    assert res_other.status_code == 403


# ==============================================================================
# 6. RECTOR -> COORDINATOR
# ==============================================================================
@pytest.mark.asyncio
async def test_06_rector_provisions_coordinator(
    client: AsyncClient, nta08_fixture: dict[str, Any], db_session: AsyncSession
):
    rector_headers = nta08_fixture["rector_headers"]
    inst_baq = nta08_fixture["inst_baq"]
    coord_user = nta08_fixture["coord_user"]

    # Vacate coordinator slot in inst_baq to comply with NTA-10-R10 exclusivity
    await db_session.execute(
        update(User).where(User.id == coord_user.id).values(is_active=False)
    )
    await db_session.execute(
        update(UserRole).where(UserRole.user_id == coord_user.id).values(is_active=False)
    )
    await db_session.commit()

    payload = {
        "email": f"coord_new_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "first_name": "Alfonso",
        "last_name": "Lopez",
        "document_type": "CC",
        "document_number": _rand_doc(),
    }
    res = await client.post("/api/v1/coordinators", json=payload, headers=rector_headers)
    assert res.status_code == 201
    assert res.json()["role"] == "coordinator"
    assert res.json()["institution_id"] == str(inst_baq.id)


# ==============================================================================
# 7. RECTOR -> TEACHER
# ==============================================================================
@pytest.mark.asyncio
async def test_07_rector_provisions_teacher(
    client: AsyncClient, nta08_fixture: dict[str, Any]
):
    rector_headers = nta08_fixture["rector_headers"]
    inst_baq = nta08_fixture["inst_baq"]

    payload = {
        "provision_account": True,
        "contract_type": "PROPIEDAD",
        "new_user": {
            "first_name": "Gabriel",
            "last_name": "Garcia",
            "email": f"teacher_gabo_{uuid.uuid4().hex[:6]}@pevn.edu.co",
            "document_type": "CC",
            "document_number": _rand_doc(),
        },
    }
    res = await client.post("/api/v1/teachers", json=payload, headers=rector_headers)
    assert res.status_code == 201
    assert res.json()["institution_id"] == str(inst_baq.id)


# ==============================================================================
# 8. RECTOR -> STUDENT
# ==============================================================================
@pytest.mark.asyncio
async def test_08_rector_provisions_student(
    client: AsyncClient, nta08_fixture: dict[str, Any]
):
    rector_headers = nta08_fixture["rector_headers"]
    inst_baq = nta08_fixture["inst_baq"]

    payload = {
        "code_simat": f"SIMAT{secrets.randbelow(900000) + 100000}",
        "birth_date": "2010-02-02",
        "gender": "M",
        "new_user": {
            "first_name": "Shakira",
            "last_name": "Mebarak",
            "document_type": "TI",
            "document_number": _rand_doc(),
            "email": f"student_shak_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        },
    }
    res = await client.post("/api/v1/students", json=payload, headers=rector_headers)
    assert res.status_code == 201
    assert res.json()["institution_id"] == str(inst_baq.id)


# ==============================================================================
# 9. COORDINATOR -> TEACHER (RECTOR-CONTROLLED DELEGATION)
# ==============================================================================
@pytest.mark.asyncio
async def test_09_coordinator_provisions_teacher(
    client: AsyncClient, nta08_fixture: dict[str, Any]
):
    coord_headers = nta08_fixture["coord_headers"]
    rector_headers = nta08_fixture["rector_headers"]
    inst_baq = nta08_fixture["inst_baq"]

    payload = {
        "provision_account": True,
        "contract_type": "PROPIEDAD",
        "new_user": {
            "first_name": "Alvaro",
            "last_name": "Cepeda",
            "email": f"teacher_cepeda_{uuid.uuid4().hex[:6]}@pevn.edu.co",
            "document_type": "CC",
            "document_number": _rand_doc(),
        },
    }

    # 1. When delegation is disabled (default), Coordinator is blocked -> 403
    res_blocked = await client.post("/api/v1/teachers", json=payload, headers=coord_headers)
    assert res_blocked.status_code == 403
    assert res_blocked.json()["error"]["code"] == "PERMISSION_DENIED"

    # 2. Rector enables coordinator delegation for their institution
    patch_res = await client.patch(
        f"/api/v1/institutions/{inst_baq.id}/settings/coordinator-delegation",
        json={"coordinator_delegation_enabled": True},
        headers=rector_headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["coordinator_delegation_enabled"] is True

    # 3. With delegation enabled, Coordinator operation succeeds -> 201
    res_allowed = await client.post("/api/v1/teachers", json=payload, headers=coord_headers)
    assert res_allowed.status_code == 201
    assert res_allowed.json()["institution_id"] == str(inst_baq.id)

    # 4. Rector disables delegation -> Coordinator immediately blocked again
    patch_disable = await client.patch(
        f"/api/v1/institutions/{inst_baq.id}/settings/coordinator-delegation",
        json={"coordinator_delegation_enabled": False},
        headers=rector_headers,
    )
    assert patch_disable.status_code == 200
    assert patch_disable.json()["coordinator_delegation_enabled"] is False

    res_blocked_again = await client.post(
        "/api/v1/teachers",
        json={
            **payload,
            "new_user": {
                **payload["new_user"],
                "email": f"teacher_blocked_{uuid.uuid4().hex[:6]}@pevn.edu.co",
                "document_number": _rand_doc(),
            },
        },
        headers=coord_headers,
    )
    assert res_blocked_again.status_code == 403


# ==============================================================================
# 10. COORDINATOR -> STUDENT (RECTOR-CONTROLLED DELEGATION)
# ==============================================================================
@pytest.mark.asyncio
async def test_10_coordinator_provisions_student(
    client: AsyncClient, nta08_fixture: dict[str, Any]
):
    coord_headers = nta08_fixture["coord_headers"]
    rector_headers = nta08_fixture["rector_headers"]
    inst_baq = nta08_fixture["inst_baq"]

    payload = {
        "code_simat": f"SIMAT{secrets.randbelow(900000) + 100000}",
        "birth_date": "2011-07-10",
        "gender": "F",
        "new_user": {
            "first_name": "Sofia",
            "last_name": "Vergara",
            "document_type": "TI",
            "document_number": _rand_doc(),
            "email": f"student_sofia_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        },
    }

    # 1. When delegation is disabled, Coordinator blocked -> 403
    res_blocked = await client.post("/api/v1/students", json=payload, headers=coord_headers)
    assert res_blocked.status_code == 403

    # 2. Rector enables delegation
    patch_res = await client.patch(
        f"/api/v1/institutions/{inst_baq.id}/settings/coordinator-delegation",
        json={"coordinator_delegation_enabled": True},
        headers=rector_headers,
    )
    assert patch_res.status_code == 200

    # 3. Coordinator operation succeeds -> 201
    res = await client.post("/api/v1/students", json=payload, headers=coord_headers)
    assert res.status_code == 201
    assert res.json()["institution_id"] == str(inst_baq.id)

    # 4. Rector disables delegation
    await client.patch(
        f"/api/v1/institutions/{inst_baq.id}/settings/coordinator-delegation",
        json={"coordinator_delegation_enabled": False},
        headers=rector_headers,
    )


# ==============================================================================
# 11. GUARDIAN WORKFLOW (RECTOR-CONTROLLED DELEGATION)
# ==============================================================================
@pytest.mark.asyncio
async def test_11_guardian_workflow(
    client: AsyncClient, nta08_fixture: dict[str, Any]
):
    coord_headers = nta08_fixture["coord_headers"]
    rector_headers = nta08_fixture["rector_headers"]
    inst_baq = nta08_fixture["inst_baq"]

    # 1. Blocked while delegation is disabled -> 403
    stu_payload = {
        "code_simat": f"SIMAT{secrets.randbelow(900000) + 100000}",
        "birth_date": "2012-05-15",
        "gender": "M",
        "new_user": {
            "first_name": "Nino",
            "last_name": "Valderrama",
            "document_type": "TI",
            "document_number": _rand_doc(),
            "email": f"student_nino_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        },
    }
    res_blocked = await client.post("/api/v1/students", json=stu_payload, headers=coord_headers)
    assert res_blocked.status_code == 403

    # 2. Rector enables delegation
    await client.patch(
        f"/api/v1/institutions/{inst_baq.id}/settings/coordinator-delegation",
        json={"coordinator_delegation_enabled": True},
        headers=rector_headers,
    )

    # 3. Create student
    stu_res = await client.post(
        "/api/v1/students",
        json=stu_payload,
        headers=coord_headers,
    )
    assert stu_res.status_code == 201
    student_id = stu_res.json()["id"]

    # 4. Provision Guardian
    g_res = await client.post(
        "/api/v1/guardians",
        json={
            "first_name": "Padre",
            "last_name": "Valderrama",
            "document_type": "CC",
            "document_number": _rand_doc(),
            "email": f"guardian_{uuid.uuid4().hex[:6]}@pevn.edu.co",
            "phone": "3001234567",
            "relationship_type": "PADRE",
        },
        headers=coord_headers,
    )
    assert g_res.status_code == 201
    guardian_id = g_res.json()["id"]

    # 5. Link student to guardian
    link_res = await client.post(
        f"/api/v1/guardians/{guardian_id}/students/{student_id}",
        json={
            "relationship_type": "PADRE",
            "is_authorized_pickup": True,
        },
        headers=coord_headers,
    )
    assert link_res.status_code in (200, 201)

    # 6. Rector disables delegation
    await client.patch(
        f"/api/v1/institutions/{inst_baq.id}/settings/coordinator-delegation",
        json={"coordinator_delegation_enabled": False},
        headers=rector_headers,
    )

    # 7. Subsequent linking attempts by coordinator blocked immediately
    link_blocked = await client.post(
        f"/api/v1/guardians/{guardian_id}/students/{student_id}",
        json={
            "relationship_type": "PADRE",
            "is_authorized_pickup": True,
        },
        headers=coord_headers,
    )
    assert link_blocked.status_code == 403



# ==============================================================================
# 12. CROSS-DEPARTMENT REJECTION (ANTI-IDOR)
# ==============================================================================
@pytest.mark.asyncio
async def test_12_cross_department_rejection(
    client: AsyncClient, nta08_fixture: dict[str, Any]
):
    dept_admin_headers = nta08_fixture["dept_admin_headers"]  # Atlántico
    inst_faca = nta08_fixture["inst_faca"]  # Cundinamarca

    # Cross-department read blocked -> 403
    res = await client.get(f"/api/v1/institutions/{inst_faca.id}", headers=dept_admin_headers)
    assert res.status_code == 403


# ==============================================================================
# 13. CROSS-MUNICIPALITY REJECTION (ANTI-IDOR)
# ==============================================================================
@pytest.mark.asyncio
async def test_13_cross_municipality_rejection(
    client: AsyncClient, nta08_fixture: dict[str, Any]
):
    muni_admin_headers = nta08_fixture["muni_admin_headers"]  # Barranquilla
    inst_faca = nta08_fixture["inst_faca"]  # Facatativá

    # Cross-municipality read blocked -> 403
    res = await client.get(f"/api/v1/institutions/{inst_faca.id}", headers=muni_admin_headers)
    assert res.status_code == 403


# ==============================================================================
# 14. CROSS-INSTITUTION REJECTION (ANTI-IDOR)
# ==============================================================================
@pytest.mark.asyncio
async def test_14_cross_institution_rejection(
    client: AsyncClient, nta08_fixture: dict[str, Any]
):
    rector_headers = nta08_fixture["rector_headers"]  # Barranquilla institution
    inst_faca = nta08_fixture["inst_faca"]  # Facatativá institution

    # Rector cannot query other institution -> 403
    res = await client.get(f"/api/v1/institutions/{inst_faca.id}", headers=rector_headers)
    assert res.status_code == 403


# ==============================================================================
# 15. ROLE ESCALATION REJECTION
# ==============================================================================
@pytest.mark.asyncio
async def test_15_role_escalation_rejection(
    client: AsyncClient, nta08_fixture: dict[str, Any]
):
    teacher_headers = nta08_fixture["teacher_headers"]
    coord_headers = nta08_fixture["coord_headers"]
    inst_baq = nta08_fixture["inst_baq"]

    # 1. Teacher cannot invite Rector -> 403
    res_teacher = await client.post(
        f"/api/v1/institutions/{inst_baq.id}/rector-invitation",
        json={
            "first_name": "Escalated",
            "last_name": "Rector",
            "document_type": "CC",
            "document_number": _rand_doc(),
            "email": "escalated@pevn.edu.co",
        },
        headers=teacher_headers,
    )
    assert res_teacher.status_code == 403

    # 2. Coordinator cannot invite Rector -> 403
    res_coord = await client.post(
        f"/api/v1/institutions/{inst_baq.id}/rector-invitation",
        json={
            "first_name": "Escalated",
            "last_name": "Rector",
            "document_type": "CC",
            "document_number": _rand_doc(),
            "email": "escalated@pevn.edu.co",
        },
        headers=coord_headers,
    )
    assert res_coord.status_code == 403

    # 3. Generic role patch endpoint does NOT exist -> 404 or 405
    res_patch = await client.patch(
        f"/api/v1/users/{uuid.uuid4()}/role",
        json={"role": "superadmin"},
        headers=teacher_headers,
    )
    assert res_patch.status_code in (404, 405)


# ==============================================================================
# 16. SCOPE TAMPERING REJECTION
# ==============================================================================
@pytest.mark.asyncio
async def test_16_scope_tampering_rejection(
    client: AsyncClient, nta08_fixture: dict[str, Any]
):
    dept_admin_headers = nta08_fixture["dept_admin_headers"]  # Atlántico
    muni_faca = nta08_fixture["muni_facatativa"]  # In Cundinamarca

    # Tampering query parameter with another department's municipality -> 403
    res = await client.get(
        f"/api/v1/municipality-admins/municipalities?department_id={nta08_fixture['dept_cun'].id}",
        headers=dept_admin_headers,
    )
    assert res.status_code == 403


# ==============================================================================
# 17. RECTOR SUCCESSION (ONE ACTIVE RECTOR ENFORCEMENT)
# ==============================================================================
@pytest.mark.asyncio
async def test_17_rector_succession(
    client: AsyncClient, nta08_fixture: dict[str, Any], db_session: AsyncSession
):
    super_headers = nta08_fixture["superadmin_headers"]
    inst_baq = nta08_fixture["inst_baq"]

    # 1. Active Rector exists
    # Revoke active rector
    revoke_payload = {
        "reason": "RETIRO_VOLUNTARIO",
        "justification": "Sucesión controlada por renuncia voluntaria.",
    }
    rev_res = await client.post(
        f"/api/v1/institutions/{inst_baq.id}/rector/revoke",
        json=revoke_payload,
        headers=super_headers,
    )
    assert rev_res.status_code == 200

    # 2. Invite new Rector
    inv_payload = {
        "first_name": "Nuevo",
        "last_name": "Rector",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "email": f"nuevo_rector_{uuid.uuid4().hex[:6]}@pevn.edu.co",
    }
    inv_res = await client.post(
        f"/api/v1/institutions/{inst_baq.id}/rector-invitation",
        json=inv_payload,
        headers=super_headers,
    )
    assert inv_res.status_code == 201
    raw_token = inv_res.json()["raw_invitation_token"]

    # 3. Accept invitation
    acc_res = await client.post(
        "/api/v1/auth/accept-invitation",
        json={
            "token": raw_token,
            "password": "RectorPassword2026*!",
            "password_confirmation": "RectorPassword2026*!",
        },
    )
    assert acc_res.status_code == 200

    # 4. Invariant check: exactly ONE active rector for inst_baq
    rector_role = (await db_session.execute(select(Role).where(Role.name == "rector"))).scalar_one()
    active_rectors = (
        await db_session.execute(
            select(UserRole).where(
                UserRole.institution_id == inst_baq.id,
                UserRole.role_id == rector_role.id,
                UserRole.is_active == True,
            )
        )
    ).scalars().all()
    assert len(active_rectors) == 1


# ==============================================================================
# 18. INVITATION REPLAY REJECTION
# ==============================================================================
@pytest.mark.asyncio
async def test_18_invitation_replay_rejection(
    client: AsyncClient, nta08_fixture: dict[str, Any], db_session: AsyncSession
):
    super_headers = nta08_fixture["superadmin_headers"]
    inst_baq = nta08_fixture["inst_baq"]

    # Revoke to free up institution
    await client.post(
        f"/api/v1/institutions/{inst_baq.id}/rector/revoke",
        json={"reason": "OTRO", "justification": "Replay test."},
        headers=super_headers,
    )

    inv_res = await client.post(
        f"/api/v1/institutions/{inst_baq.id}/rector-invitation",
        json={
            "first_name": "Replay",
            "last_name": "Test",
            "document_type": "CC",
            "document_number": _rand_doc(),
            "email": f"replay_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        },
        headers=super_headers,
    )
    raw_token = inv_res.json()["raw_invitation_token"]

    # First acceptance succeeds
    acc_1 = await client.post(
        "/api/v1/auth/accept-invitation",
        json={
            "token": raw_token,
            "password": "Password123*#",
            "password_confirmation": "Password123*#",
        },
    )
    assert acc_1.status_code == 200

    # Replay acceptance fails (400, 409, or 422)
    acc_2 = await client.post(
        "/api/v1/auth/accept-invitation",
        json={
            "token": raw_token,
            "password": "Password123*#",
            "password_confirmation": "Password123*#",
        },
    )
    assert acc_2.status_code in (400, 409, 422)


# ==============================================================================
# 19. INVITATION EXPIRATION
# ==============================================================================
@pytest.mark.asyncio
async def test_19_invitation_expiration(
    client: AsyncClient, nta08_fixture: dict[str, Any], db_session: AsyncSession
):
    super_headers = nta08_fixture["superadmin_headers"]
    inst_faca_vacant = nta08_fixture["inst_faca_vacant"]

    inv_res = await client.post(
        f"/api/v1/institutions/{inst_faca_vacant.id}/rector-invitation",
        json={
            "first_name": "Expire",
            "last_name": "Test",
            "document_type": "CC",
            "document_number": _rand_doc(),
            "email": f"expire_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        },
        headers=super_headers,
    )
    raw_token = inv_res.json()["raw_invitation_token"]
    inv_id = uuid.UUID(inv_res.json()["invitation_id"])

    # Force invitation to expired in DB
    await db_session.execute(
        update(RectorInvitation)
        .where(RectorInvitation.id == inv_id)
        .values(expires_at=datetime.now(UTC) - timedelta(days=2))
    )
    await db_session.commit()

    # Expired token rejected
    acc = await client.post(
        "/api/v1/auth/accept-invitation",
        json={
            "token": raw_token,
            "password": "Password123*#",
            "password_confirmation": "Password123*#",
        },
    )
    assert acc.status_code in (400, 409, 410, 422)


# ==============================================================================
# 20. SESSION INVALIDATION AFTER REVOCATION
# ==============================================================================
@pytest.mark.asyncio
async def test_20_session_invalidation_after_revocation(
    client: AsyncClient, nta08_fixture: dict[str, Any], db_session: AsyncSession
):
    super_headers = nta08_fixture["superadmin_headers"]
    muni_admin_user = nta08_fixture["muni_admin_user"]

    target_user_id = muni_admin_user.id

    # Insert active refresh token for muni_admin_user
    rf = RefreshToken(
        user_id=target_user_id,
        token_hash=hash_token("test_refresh_token_string"),
        family_id=uuid.uuid4(),
        expires_at=datetime.now(UTC) + timedelta(days=7),
        is_revoked=False,
    )
    db_session.add(rf)
    await db_session.commit()

    # Deactivate Municipality Admin account
    deact_res = await client.patch(
        f"/api/v1/municipality-admins/{target_user_id}/status",
        json={"is_active": False, "reason": "Suspensión administrativa."},
        headers=super_headers,
    )
    assert deact_res.status_code == 200

    # Verify refresh token was revoked
    is_revoked = (
        await db_session.execute(
            select(RefreshToken.is_revoked).where(RefreshToken.user_id == target_user_id)
        )
    ).scalar_one()
    assert is_revoked is True


# ==============================================================================
# 21. COORDINATOR CANNOT CREATE COORDINATOR (NO PEER PROVISIONING)
# ==============================================================================
@pytest.mark.asyncio
async def test_21_coordinator_cannot_create_coordinator(
    client: AsyncClient, nta08_fixture: dict[str, Any]
):
    coord_headers = nta08_fixture["coord_headers"]

    payload = {
        "first_name": "Peer",
        "last_name": "Coordinator",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "email": f"peer_coord_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "is_active": True,
    }
    res = await client.post("/api/v1/coordinators", json=payload, headers=coord_headers)
    assert res.status_code == 403


# ==============================================================================
# 22. COORDINATOR CANNOT CREATE TERRITORIAL OR NATIONAL ADMINISTRATORS
# ==============================================================================
@pytest.mark.asyncio
async def test_22_coordinator_cannot_create_territorial_admins(
    client: AsyncClient, nta08_fixture: dict[str, Any]
):
    coord_headers = nta08_fixture["coord_headers"]
    dept_atl = nta08_fixture["dept_atl"]
    muni_baq = nta08_fixture["muni_barranquilla"]

    # 1. Coordinator cannot create Department Admin -> 403
    res_dept = await client.post(
        "/api/v1/department-admins",
        json={
            "department_id": str(dept_atl.id),
            "email": f"escalated_dept_{uuid.uuid4().hex[:6]}@pevn.edu.co",
            "first_name": "Escalated",
            "last_name": "DeptAdmin",
            "document_type": "CC",
            "document_number": _rand_doc(),
        },
        headers=coord_headers,
    )
    assert res_dept.status_code == 403

    # 2. Coordinator cannot create Municipality Admin -> 403
    res_muni = await client.post(
        "/api/v1/municipality-admins",
        json={
            "municipality_id": str(muni_baq.id),
            "email": f"escalated_muni_{uuid.uuid4().hex[:6]}@pevn.edu.co",
            "first_name": "Escalated",
            "last_name": "MuniAdmin",
            "document_type": "CC",
            "document_number": _rand_doc(),
        },
        headers=coord_headers,
    )
    assert res_muni.status_code == 403


# ==============================================================================
# 23. STUDENT CANNOT CREATE OR LINK GUARDIANS
# ==============================================================================
@pytest.mark.asyncio
async def test_23_student_cannot_manage_guardians(
    client: AsyncClient, nta08_fixture: dict[str, Any]
):
    student_headers = nta08_fixture["student_headers"]

    # 1. Student cannot create guardian -> 403
    res_create = await client.post(
        "/api/v1/guardians",
        json={
            "first_name": "Fake",
            "last_name": "Guardian",
            "document_type": "CC",
            "document_number": _rand_doc(),
            "email": f"fake_guard_{uuid.uuid4().hex[:6]}@pevn.edu.co",
            "relationship_type": "PADRE",
        },
        headers=student_headers,
    )
    assert res_create.status_code == 403

    # 2. Student cannot link guardian -> 403
    fake_gid = uuid.uuid4()
    fake_sid = uuid.uuid4()
    res_link = await client.post(
        f"/api/v1/guardians/{fake_gid}/students/{fake_sid}",
        json={"relationship_type": "PADRE"},
        headers=student_headers,
    )
    assert res_link.status_code == 403


# ==============================================================================
# 24. CROSS-INSTITUTION GUARDIAN LINKAGE REJECTION
# ==============================================================================
@pytest.mark.asyncio
async def test_24_cross_institution_guardian_link_rejection(
    client: AsyncClient, nta08_fixture: dict[str, Any]
):
    coord_headers = nta08_fixture["coord_headers"]  # inst_baq
    rector_headers = nta08_fixture["rector_headers"]
    inst_baq = nta08_fixture["inst_baq"]

    # Enable delegation so Coordinator is authorized to create student
    await client.patch(
        f"/api/v1/institutions/{inst_baq.id}/settings/coordinator-delegation",
        json={"coordinator_delegation_enabled": True},
        headers=rector_headers,
    )

    # Create student in inst_baq
    stu_res = await client.post(
        "/api/v1/students",
        json={
            "code_simat": f"SIMAT{secrets.randbelow(900000) + 100000}",
            "birth_date": "2012-05-15",
            "gender": "M",
            "new_user": {
                "first_name": "Estudiante",
                "last_name": "Baq",
                "document_type": "TI",
                "document_number": _rand_doc(),
                "email": f"student_baq_{uuid.uuid4().hex[:6]}@pevn.edu.co",
            },
        },
        headers=coord_headers,
    )
    assert stu_res.status_code == 201
    student_id = stu_res.json()["id"]

    # Attempt to link to a non-existent / cross-institution guardian -> 404 or 403
    foreign_guardian_id = uuid.uuid4()
    res = await client.post(
        f"/api/v1/guardians/{foreign_guardian_id}/students/{student_id}",
        json={"relationship_type": "PADRE"},
        headers=coord_headers,
    )
    assert res.status_code in (403, 404)

    # Reset delegation back to default disabled
    await client.patch(
        f"/api/v1/institutions/{inst_baq.id}/settings/coordinator-delegation",
        json={"coordinator_delegation_enabled": False},
        headers=rector_headers,
    )


# ==============================================================================
# 25. TERRITORIAL ADMINISTRATORS CANNOT DIRECTLY CREATE INSTITUTIONAL ACTORS
# ==============================================================================
@pytest.mark.asyncio
async def test_25_territorial_admins_cannot_create_institutional_actors(
    client: AsyncClient, nta08_fixture: dict[str, Any]
):
    nat_admin_headers = nta08_fixture["nat_admin_headers"]
    dept_admin_headers = nta08_fixture["dept_admin_headers"]
    muni_admin_headers = nta08_fixture["muni_admin_headers"]
    inst_baq = nta08_fixture["inst_baq"]

    teacher_payload = {
        "provision_account": True,
        "contract_type": "PROPIEDAD",
        "new_user": {
            "first_name": "Direct",
            "last_name": "Teacher",
            "email": f"direct_t_{uuid.uuid4().hex[:6]}@pevn.edu.co",
            "document_type": "CC",
            "document_number": _rand_doc(),
        },
    }

    # 1. National Admin cannot create teachers directly -> 403
    res_nat = await client.post(
        f"/api/v1/teachers?institution_id={inst_baq.id}",
        json=teacher_payload,
        headers=nat_admin_headers,
    )
    assert res_nat.status_code == 403

    # 2. Department Admin cannot create teachers directly -> 403
    res_dept = await client.post(
        f"/api/v1/teachers?institution_id={inst_baq.id}",
        json=teacher_payload,
        headers=dept_admin_headers,
    )
    assert res_dept.status_code == 403

    # 3. Municipality Admin cannot create teachers directly -> 403
    res_muni = await client.post(
        f"/api/v1/teachers?institution_id={inst_baq.id}",
        json=teacher_payload,
        headers=muni_admin_headers,
    )
    assert res_muni.status_code == 403


# ==============================================================================
# 26. SUPERADMIN EMERGENCY OVERRIDE DEDICATED AUDIT LOGGING
# ==============================================================================
@pytest.mark.asyncio
async def test_26_superadmin_emergency_override_audit_logging(
    client: AsyncClient, nta08_fixture: dict[str, Any], db_session: AsyncSession
):
    super_headers = nta08_fixture["superadmin_headers"]
    inst_baq_vac = nta08_fixture["inst_baq_vacant"]

    # 1. SuperAdmin invites Rector (emergency override path)
    super_rector_email = f"super_rector_{uuid.uuid4().hex[:6]}@pevn.edu.co"
    res_super = await client.post(
        f"/api/v1/institutions/{inst_baq_vac.id}/rector-invitation",
        json={
            "first_name": "Emergency",
            "last_name": "Rector",
            "document_type": "CC",
            "document_number": _rand_doc(),
            "email": super_rector_email,
        },
        headers=super_headers,
    )
    assert res_super.status_code == 201

    # 2. Check that SUPERADMIN_EMERGENCY_ROLE_PROVISIONING audit log was created
    audit_stmt = select(AuditLog).where(
        AuditLog.event_type == AuditEventType.SUPERADMIN_EMERGENCY_ROLE_PROVISIONING.value
    )
    emergency_logs = (await db_session.execute(audit_stmt)).scalars().all()
    assert len(emergency_logs) >= 1

    latest_override = emergency_logs[-1]
    assert latest_override.metadata_json is not None
    assert latest_override.metadata_json.get("authority_level") == "superadmin_emergency"
    assert latest_override.metadata_json.get("action") == "invite_rector"
    # Verify no raw passwords or sensitive credentials leaked
    assert "password" not in latest_override.metadata_json


# ==============================================================================
# 27. NATIONAL ADMIN SUPERVISORY RECTOR INTERVENTION
# ==============================================================================
@pytest.mark.asyncio
async def test_27_national_admin_supervisory_rector_intervention(
    client: AsyncClient, nta08_fixture: dict[str, Any], db_session: AsyncSession
):
    nat_headers = nta08_fixture["nat_admin_headers"]
    inst_faca_vac = nta08_fixture["inst_faca_vacant"]

    nat_rector_email = f"nat_rector_{uuid.uuid4().hex[:6]}@pevn.edu.co"
    res_nat = await client.post(
        f"/api/v1/institutions/{inst_faca_vac.id}/rector-invitation",
        json={
            "first_name": "Supervisory",
            "last_name": "Rector",
            "document_type": "CC",
            "document_number": _rand_doc(),
            "email": nat_rector_email,
        },
        headers=nat_headers,
    )
    assert res_nat.status_code == 201

    # Verify audit log recorded "national_supervisory" authority_level
    audit_stmt = select(AuditLog).where(
        AuditLog.event_type == AuditEventType.RECTOR_INVITED.value,
        AuditLog.target_id == res_nat.json()["user_id"],
    )
    log = (await db_session.execute(audit_stmt)).scalar_one_or_none()
    assert log is not None
    assert log.metadata_json.get("authority_level") == "national_supervisory"


# ==============================================================================
# 28. DELEGATION SETTING LIFECYCLE, AUDIT & CROSS-TENANT ISOLATION
# ==============================================================================
@pytest.mark.asyncio
async def test_28_delegation_setting_lifecycle_and_isolation(
    client: AsyncClient, nta08_fixture: dict[str, Any], db_session: AsyncSession
):
    rector_headers = nta08_fixture["rector_headers"]
    coord_headers = nta08_fixture["coord_headers"]
    inst_baq = nta08_fixture["inst_baq"]
    inst_faca = nta08_fixture["inst_faca"]

    # 1. Setting defaults to disabled (False)
    get_res = await client.get(
        f"/api/v1/institutions/{inst_baq.id}/settings/coordinator-delegation",
        headers=rector_headers,
    )
    assert get_res.status_code == 200
    assert get_res.json()["coordinator_delegation_enabled"] is False

    # 2. Rector enables setting for own institution
    enable_res = await client.patch(
        f"/api/v1/institutions/{inst_baq.id}/settings/coordinator-delegation",
        json={"coordinator_delegation_enabled": True},
        headers=rector_headers,
    )
    assert enable_res.status_code == 200
    assert enable_res.json()["coordinator_delegation_enabled"] is True

    # 3. Rector disables setting for own institution
    disable_res = await client.patch(
        f"/api/v1/institutions/{inst_baq.id}/settings/coordinator-delegation",
        json={"coordinator_delegation_enabled": False},
        headers=rector_headers,
    )
    assert disable_res.status_code == 200
    assert disable_res.json()["coordinator_delegation_enabled"] is False

    # 4. Rector CANNOT modify or read another institution's setting -> 403
    cross_get = await client.get(
        f"/api/v1/institutions/{inst_faca.id}/settings/coordinator-delegation",
        headers=rector_headers,
    )
    assert cross_get.status_code == 403
    assert cross_get.json()["error"]["code"] == "PERMISSION_DENIED"

    cross_res = await client.patch(
        f"/api/v1/institutions/{inst_faca.id}/settings/coordinator-delegation",
        json={"coordinator_delegation_enabled": True},
        headers=rector_headers,
    )
    assert cross_res.status_code == 403
    assert cross_res.json()["error"]["code"] == "PERMISSION_DENIED"

    # 5. Unauthorized roles CANNOT view or modify setting -> 403
    teacher_headers = nta08_fixture["teacher_headers"]
    student_headers = nta08_fixture["student_headers"]
    superadmin_headers = nta08_fixture["superadmin_headers"]

    # Coordinator cannot read or modify
    coord_get = await client.get(
        f"/api/v1/institutions/{inst_baq.id}/settings/coordinator-delegation",
        headers=coord_headers,
    )
    assert coord_get.status_code == 403

    coord_mod = await client.patch(
        f"/api/v1/institutions/{inst_baq.id}/settings/coordinator-delegation",
        json={"coordinator_delegation_enabled": True},
        headers=coord_headers,
    )
    assert coord_mod.status_code == 403

    # Teacher cannot read or modify
    teacher_get = await client.get(
        f"/api/v1/institutions/{inst_baq.id}/settings/coordinator-delegation",
        headers=teacher_headers,
    )
    assert teacher_get.status_code == 403

    teacher_mod = await client.patch(
        f"/api/v1/institutions/{inst_baq.id}/settings/coordinator-delegation",
        json={"coordinator_delegation_enabled": True},
        headers=teacher_headers,
    )
    assert teacher_mod.status_code == 403

    # Student cannot read or modify
    student_get = await client.get(
        f"/api/v1/institutions/{inst_baq.id}/settings/coordinator-delegation",
        headers=student_headers,
    )
    assert student_get.status_code == 403

    student_mod = await client.patch(
        f"/api/v1/institutions/{inst_baq.id}/settings/coordinator-delegation",
        json={"coordinator_delegation_enabled": True},
        headers=student_headers,
    )
    assert student_mod.status_code == 403

    # Institution Admin cannot read or modify
    create_actor = nta08_fixture["create_actor"]
    _, _, inst_admin_headers = await create_actor("institution_admin", inst_id=inst_baq.id)
    ia_get = await client.get(
        f"/api/v1/institutions/{inst_baq.id}/settings/coordinator-delegation",
        headers=inst_admin_headers,
    )
    assert ia_get.status_code == 403

    ia_patch = await client.patch(
        f"/api/v1/institutions/{inst_baq.id}/settings/coordinator-delegation",
        json={"coordinator_delegation_enabled": True},
        headers=inst_admin_headers,
    )
    assert ia_patch.status_code == 403

    # Territorial admins (National, Department, Municipality) cannot read or modify
    nat_admin_headers = nta08_fixture["nat_admin_headers"]
    dept_admin_headers = nta08_fixture["dept_admin_headers"]
    muni_admin_headers = nta08_fixture["muni_admin_headers"]

    for t_headers in [nat_admin_headers, dept_admin_headers, muni_admin_headers]:
        t_get = await client.get(
            f"/api/v1/institutions/{inst_baq.id}/settings/coordinator-delegation",
            headers=t_headers,
        )
        assert t_get.status_code == 403

        t_patch = await client.patch(
            f"/api/v1/institutions/{inst_baq.id}/settings/coordinator-delegation",
            json={"coordinator_delegation_enabled": True},
            headers=t_headers,
        )
        assert t_patch.status_code == 403

    # 6. SuperAdmin platform override CAN read and modify
    super_get = await client.get(
        f"/api/v1/institutions/{inst_baq.id}/settings/coordinator-delegation",
        headers=superadmin_headers,
    )
    assert super_get.status_code == 200

    super_mod = await client.patch(
        f"/api/v1/institutions/{inst_baq.id}/settings/coordinator-delegation",
        json={"coordinator_delegation_enabled": False},
        headers=superadmin_headers,
    )
    assert super_mod.status_code == 200
    assert super_mod.json()["coordinator_delegation_enabled"] is False

    # 7. Audit trail verification
    audit_stmt = select(AuditLog).where(
        AuditLog.event_type == AuditEventType.COORDINATOR_DELEGATION_SETTING_UPDATED.value,
        AuditLog.institution_id == inst_baq.id,
    )
    audit_logs = (await db_session.execute(audit_stmt)).scalars().all()
    assert len(audit_logs) >= 2  # At least the enable and disable actions
    latest_audit = audit_logs[-1]
    assert latest_audit.metadata_json.get("outcome") == "success"


# ==============================================================================
# 29. SERVER-SIDE ENFORCEMENT & RECTOR INVARIANCE
# ==============================================================================
@pytest.mark.asyncio
async def test_29_coordinator_management_operations_blocked_when_delegation_disabled(
    client: AsyncClient, nta08_fixture: dict[str, Any]
):
    coord_headers = nta08_fixture["coord_headers"]
    rector_headers = nta08_fixture["rector_headers"]
    inst_baq = nta08_fixture["inst_baq"]

    # Ensure delegation is explicitly disabled
    await client.patch(
        f"/api/v1/institutions/{inst_baq.id}/settings/coordinator-delegation",
        json={"coordinator_delegation_enabled": False},
        headers=rector_headers,
    )

    # 1. Coordinator cannot create teacher -> 403
    teacher_payload = {
        "provision_account": True,
        "contract_type": "PROPIEDAD",
        "new_user": {
            "first_name": "Test",
            "last_name": "Teacher",
            "email": f"t_blocked_{uuid.uuid4().hex[:6]}@pevn.edu.co",
            "document_type": "CC",
            "document_number": _rand_doc(),
        },
    }
    res_t = await client.post("/api/v1/teachers", json=teacher_payload, headers=coord_headers)
    assert res_t.status_code == 403

    # 2. Coordinator cannot create student -> 403
    student_payload = {
        "code_simat": f"SIMAT{secrets.randbelow(900000) + 100000}",
        "birth_date": "2013-01-01",
        "gender": "M",
        "new_user": {
            "first_name": "Test",
            "last_name": "Student",
            "document_type": "TI",
            "document_number": _rand_doc(),
            "email": f"s_blocked_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        },
    }
    res_s = await client.post("/api/v1/students", json=student_payload, headers=coord_headers)
    assert res_s.status_code == 403

    # 3. Coordinator cannot create guardian -> 403
    guardian_payload = {
        "first_name": "Test",
        "last_name": "Guardian",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "email": f"g_blocked_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "phone": "3009998877",
        "relationship_type": "MADRE",
    }
    res_g = await client.post("/api/v1/guardians", json=guardian_payload, headers=coord_headers)
    assert res_g.status_code == 403

    # 4. Invariance: RECTOR can ALWAYS create teacher, student, guardian even with delegation disabled
    rector_t = await client.post("/api/v1/teachers", json=teacher_payload, headers=rector_headers)
    assert rector_t.status_code == 201

    rector_s = await client.post("/api/v1/students", json=student_payload, headers=rector_headers)
    assert rector_s.status_code == 201

    rector_g = await client.post("/api/v1/guardians", json=guardian_payload, headers=rector_headers)
    assert rector_g.status_code == 201


# ==============================================================================
# 30. DISABLING DELEGATION PRESERVES USERS, RELATIONSHIPS & ACADEMIC DATA
# ==============================================================================
@pytest.mark.asyncio
async def test_30_disabling_delegation_preserves_existing_data(
    client: AsyncClient, nta08_fixture: dict[str, Any]
):
    coord_headers = nta08_fixture["coord_headers"]
    rector_headers = nta08_fixture["rector_headers"]
    inst_baq = nta08_fixture["inst_baq"]

    # 1. Enable delegation
    await client.patch(
        f"/api/v1/institutions/{inst_baq.id}/settings/coordinator-delegation",
        json={"coordinator_delegation_enabled": True},
        headers=rector_headers,
    )

    # 2. Coordinator provisions teacher, student, guardian, and links them
    t_payload = {
        "provision_account": True,
        "contract_type": "PROPIEDAD",
        "new_user": {
            "first_name": "Dionisio",
            "last_name": "Preserved",
            "email": f"dionisio_{uuid.uuid4().hex[:6]}@pevn.edu.co",
            "document_type": "CC",
            "document_number": _rand_doc(),
        },
    }
    res_t = await client.post("/api/v1/teachers", json=t_payload, headers=coord_headers)
    assert res_t.status_code == 201
    created_teacher_id = res_t.json()["id"]

    s_payload = {
        "code_simat": f"SIMAT{secrets.randbelow(900000) + 100000}",
        "birth_date": "2014-03-15",
        "gender": "F",
        "new_user": {
            "first_name": "Lucia",
            "last_name": "Preserved",
            "document_type": "TI",
            "document_number": _rand_doc(),
            "email": f"lucia_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        },
    }
    res_s = await client.post("/api/v1/students", json=s_payload, headers=coord_headers)
    assert res_s.status_code == 201
    created_student_id = res_s.json()["id"]

    g_payload = {
        "first_name": "Carmen",
        "last_name": "Preserved",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "email": f"carmen_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "phone": "3004445566",
        "relationship_type": "MADRE",
    }
    res_g = await client.post("/api/v1/guardians", json=g_payload, headers=coord_headers)
    assert res_g.status_code == 201
    created_guardian_id = res_g.json()["id"]

    # Link student to guardian
    link_res = await client.post(
        f"/api/v1/guardians/{created_guardian_id}/students/{created_student_id}",
        json={"relationship_type": "MADRE", "is_authorized_pickup": True},
        headers=coord_headers,
    )
    assert link_res.status_code in (200, 201)

    # 3. Rector disables delegation
    disable_res = await client.patch(
        f"/api/v1/institutions/{inst_baq.id}/settings/coordinator-delegation",
        json={"coordinator_delegation_enabled": False},
        headers=rector_headers,
    )
    assert disable_res.status_code == 200

    # 4. Verify that teacher, student, guardian, and relationship are 100% intact and readable
    get_t = await client.get(f"/api/v1/teachers/{created_teacher_id}", headers=coord_headers)
    assert get_t.status_code == 200
    assert get_t.json()["id"] == created_teacher_id

    get_s = await client.get(f"/api/v1/students/{created_student_id}", headers=coord_headers)
    assert get_s.status_code == 200
    assert get_s.json()["id"] == created_student_id

    get_g = await client.get(f"/api/v1/guardians/{created_guardian_id}", headers=coord_headers)
    assert get_g.status_code == 200
    assert get_g.json()["id"] == created_guardian_id

    get_links = await client.get(
        f"/api/v1/guardians/{created_guardian_id}/students", headers=coord_headers
    )
    assert get_links.status_code == 200
    assert len(get_links.json()) == 1
    assert get_links.json()[0]["student_id"] == created_student_id

    # 5. Verify Coordinator session is NOT deactivated or invalidated
    # Coordinator can still perform academic read operations
    list_t = await client.get("/api/v1/teachers", headers=coord_headers)
    assert list_t.status_code == 200

