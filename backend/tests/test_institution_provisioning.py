"""
PEVN Backend — Institutional Provisioning & Rector Onboarding Integration Tests

Comprehensive test suite covering:
  1. Institutional creation & DANE validation
  2. Uniqueness & automatic Sede Principal initialization
  3. National listing, filtering & pagination
  4. Operational status transitions & lifecycle
  5. Cryptographic token generation & zero-knowledge hash storage
  6. Rector single-use invitation lifecycle
  7. Replay attack prevention & expiration enforcement
  8. Argon2id credential onboarding & Rector role activation
  9. Immediate access to academic context after onboarding
  10. Multi-tenant boundary and RBAC security enforcement.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.core.security.tokens import hash_token, token_service
from app.models.institution import Campus, Institution
from app.models.invitation import RectorInvitation
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User


@pytest.fixture
async def provisioning_fixture(
    db_session: AsyncSession,
) -> dict[str, Any]:
    """Fixture providing national admin, department, municipality, and institutional users."""
    dept = Department(code="11", name="Bogotá D.C.")
    db_session.add(dept)
    await db_session.flush()

    mun = Municipality(department_id=dept.id, code="11001", name="Bogotá D.C.")
    db_session.add(mun)
    await db_session.flush()

    # Pre-existing institution for comparative testing
    existing_inst = Institution(
        municipality_id=mun.id,
        dane_code="111001000001",
        name="I.E. Existente",
        email="contacto@existente.edu.co",
        is_active=True,
    )
    db_session.add(existing_inst)
    await db_session.flush()

    # Seed roles
    superadmin_role = (
        await db_session.execute(select(Role).where(Role.name == SystemRole.SUPERADMIN.value))
    ).scalar_one()
    national_admin_role = (
        await db_session.execute(select(Role).where(Role.name == SystemRole.NATIONAL_ADMIN.value))
    ).scalar_one()
    rector_role = (
        await db_session.execute(select(Role).where(Role.name == SystemRole.RECTOR.value))
    ).scalar_one()
    teacher_role = (
        await db_session.execute(select(Role).where(Role.name == SystemRole.TEACHER.value))
    ).scalar_one()

    # Link permissions to national_admin_role and rector_role
    perms_to_link = [
        ("institutions", "create"),
        ("institutions", "read"),
        ("institutions", "update"),
        ("users", "create"),
        ("users", "read"),
        ("academic_years", "read"),
        ("academic_years", "create"),
    ]
    for r_name, a_name in perms_to_link:
        p_stmt = select(Permission).where(
            Permission.resource == r_name, Permission.action == a_name
        )
        perm = (await db_session.execute(p_stmt)).scalar_one_or_none()
        if not perm:
            perm = Permission(resource=r_name, action=a_name, description=f"{r_name}:{a_name}")
            db_session.add(perm)
            await db_session.flush()

        # Link to national admin
        rp_stmt = select(RolePermission).where(
            RolePermission.role_id == national_admin_role.id,
            RolePermission.permission_id == perm.id,
        )
        if not (await db_session.execute(rp_stmt)).scalar_one_or_none():
            db_session.add(RolePermission(role_id=national_admin_role.id, permission_id=perm.id))

        # Link to rector role
        rp_stmt_rec = select(RolePermission).where(
            RolePermission.role_id == rector_role.id,
            RolePermission.permission_id == perm.id,
        )
        if not (await db_session.execute(rp_stmt_rec)).scalar_one_or_none():
            db_session.add(RolePermission(role_id=rector_role.id, permission_id=perm.id))
    await db_session.flush()

    # National Admin User (scope: National, institution_id: None)
    national_admin_user = User(
        email="admin.nacional@pevn.edu.co",
        username="admin_nacional",
        hashed_password=password_hasher.hash("AdminNacional2026*!"),
        first_name="Admin",
        last_name="Nacional",
        document_type=DocumentType.CC,
        document_number="1000000001",
        institution_id=None,
        is_active=True,
        is_verified=True,
    )
    # Teacher User (institutional scope)
    teacher_user = User(
        email="docente@existente.edu.co",
        username="docente_test",
        hashed_password=password_hasher.hash("Docente2026*!"),
        first_name="Profesor",
        last_name="Prueba",
        document_type=DocumentType.CC,
        document_number="1000000002",
        institution_id=existing_inst.id,
        is_active=True,
        is_verified=True,
    )
    db_session.add_all([national_admin_user, teacher_user])
    await db_session.flush()

    # Assign UserRoles
    db_session.add(
        UserRole(
            user_id=national_admin_user.id,
            role_id=national_admin_role.id,
            institution_id=None,
            is_active=True,
        )
    )
    db_session.add(
        UserRole(
            user_id=teacher_user.id,
            role_id=teacher_role.id,
            institution_id=existing_inst.id,
            is_active=True,
        )
    )
    await db_session.flush()

    await db_session.commit()

    # Generate JWT Tokens
    admin_token = await token_service.create_access_token(
        subject=str(national_admin_user.id),
        additional_claims={
            "roles": [SystemRole.NATIONAL_ADMIN.value],
            "institution_id": None,
        },
    )
    teacher_token = await token_service.create_access_token(
        subject=str(teacher_user.id),
        additional_claims={
            "roles": [SystemRole.TEACHER.value],
            "institution_id": str(existing_inst.id),
        },
    )

    return {
        "department": dept,
        "municipality": mun,
        "existing_inst": existing_inst,
        "national_admin": national_admin_user,
        "teacher": teacher_user,
        "admin_headers": {"Authorization": f"Bearer {admin_token}"},
        "teacher_headers": {"Authorization": f"Bearer {teacher_token}"},
    }


# ===========================================================================
# 1. Institution Creation & DANE Catalog Tests
# ===========================================================================


async def test_provision_institution_success_national_admin(
    client: AsyncClient,
    provisioning_fixture: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    """Verify that a National Admin can provision an institution with automatic Sede Principal."""
    mun = provisioning_fixture["municipality"]
    headers = provisioning_fixture["admin_headers"]

    payload = {
        "dane_code": "111001099999",
        "name": "Institución Educativa Técnica San Juan",
        "email": "rectoria@sanjuan.edu.co",
        "phone": "+57 315 1234567",
        "address": "Carrera 7 # 32-10",
        "municipality_id": str(mun.id),
        "main_campus_name": "Sede Central San Juan",
    }

    res = await client.post("/api/v1/institutions", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["dane_code"] == "111001099999"
    assert data["name"] == "Institución Educativa Técnica San Juan"
    assert data["is_active"] is True
    assert len(data["campuses"]) == 1
    assert data["campuses"][0]["name"] == "Sede Central San Juan"
    assert data["campuses"][0]["dane_sede_code"] == "11100109999901"


async def test_provision_institution_invalid_dane_code_rejected(
    client: AsyncClient,
    provisioning_fixture: dict[str, Any],
) -> None:
    """Verify that DANE codes not conforming to exactly 12 digits are rejected with 422."""
    mun = provisioning_fixture["municipality"]
    headers = provisioning_fixture["admin_headers"]

    # Short DANE code (less than 12 digits)
    payload = {
        "dane_code": "12345",
        "name": "Colegio Inválido",
        "email": "invalid@colegio.edu.co",
        "municipality_id": str(mun.id),
    }
    res = await client.post("/api/v1/institutions", json=payload, headers=headers)
    assert res.status_code == 422


async def test_provision_institution_duplicate_dane_rejected(
    client: AsyncClient,
    provisioning_fixture: dict[str, Any],
) -> None:
    """Verify that duplicate DANE codes return HTTP 409 Conflict."""
    existing_inst = provisioning_fixture["existing_inst"]
    mun = provisioning_fixture["municipality"]
    headers = provisioning_fixture["admin_headers"]

    payload = {
        "dane_code": existing_inst.dane_code,
        "name": "Colegio Duplicado",
        "email": "duplicado@colegio.edu.co",
        "municipality_id": str(mun.id),
    }
    res = await client.post("/api/v1/institutions", json=payload, headers=headers)
    assert res.status_code == 409
    data = res.json()
    assert data["error"]["code"] == "DUPLICATE_DANE_CODE"


async def test_provision_institution_unauthorized_for_rector_or_teacher(
    client: AsyncClient,
    provisioning_fixture: dict[str, Any],
) -> None:
    """Verify that institutional actors (e.g. Teacher) cannot provision institutions."""
    mun = provisioning_fixture["municipality"]
    headers = provisioning_fixture["teacher_headers"]

    payload = {
        "dane_code": "111001088888",
        "name": "Colegio No Autorizado",
        "email": "hacker@colegio.edu.co",
        "municipality_id": str(mun.id),
    }
    res = await client.post("/api/v1/institutions", json=payload, headers=headers)
    assert res.status_code == 403
    data = res.json()
    assert data["error"]["code"] == "PERMISSION_DENIED"


# ===========================================================================
# 2. National Listing, Filtering & Status Transitions
# ===========================================================================


async def test_list_institutions_paginated_and_filtered(
    client: AsyncClient,
    provisioning_fixture: dict[str, Any],
) -> None:
    """Verify national listing endpoint with search and pagination."""
    headers = provisioning_fixture["admin_headers"]
    mun = provisioning_fixture["municipality"]

    res = await client.get(
        "/api/v1/institutions",
        params={"municipality_id": str(mun.id), "page": 1, "page_size": 10},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert data["total"] >= 1
    assert data["page"] == 1
    assert data["page_size"] == 10


async def test_update_institution_status_lifecycle(
    client: AsyncClient,
    provisioning_fixture: dict[str, Any],
) -> None:
    """Verify status transition (suspend/activate) of an institution."""
    existing_inst = provisioning_fixture["existing_inst"]
    headers = provisioning_fixture["admin_headers"]

    # Deactivate / Suspend
    res = await client.patch(
        f"/api/v1/institutions/{existing_inst.id}/status",
        json={"is_active": False},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["is_active"] is False

    # Reactivate
    res_act = await client.patch(
        f"/api/v1/institutions/{existing_inst.id}/status",
        json={"is_active": True},
        headers=headers,
    )
    assert res_act.status_code == 200
    assert res_act.json()["is_active"] is True


# ===========================================================================
# 3. Rector Onboarding & Invitation Lifecycle Tests
# ===========================================================================


async def test_invite_rector_success_and_token_hashing(
    client: AsyncClient,
    provisioning_fixture: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    """Verify issuing a rector invitation and verify raw token is never persisted in database."""
    existing_inst = provisioning_fixture["existing_inst"]
    headers = provisioning_fixture["admin_headers"]

    invite_payload = {
        "first_name": "Gabriel",
        "last_name": "García Márquez",
        "document_type": "CC",
        "document_number": "19876543",
        "email": "rector.gabo@sanjose.edu.co",
        "phone_number": "+57 301 5554433",
    }

    res = await client.post(
        f"/api/v1/institutions/{existing_inst.id}/rector-invitation",
        json=invite_payload,
        headers=headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert "invitation_id" in data
    assert "raw_invitation_token" in data
    raw_token = data["raw_invitation_token"]
    assert raw_token is not None
    assert len(raw_token) >= 32

    # Verify that in PostgreSQL only SHA-256 is stored
    invitation_id = uuid.UUID(data["invitation_id"])
    inv_stmt = select(RectorInvitation).where(RectorInvitation.id == invitation_id)
    inv_db = (await db_session.execute(inv_stmt)).scalar_one()

    # The raw token string must NOT match the stored token_hash
    assert inv_db.token_hash != raw_token
    # But the hash_token(raw_token) MUST match the stored token_hash
    assert inv_db.token_hash == hash_token(raw_token)
    assert inv_db.is_used is False
    assert inv_db.is_revoked is False


async def test_invite_rector_duplicate_active_rector_rejected(
    client: AsyncClient,
    provisioning_fixture: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    """Verify that an institution cannot have two active rectors invited simultaneously."""
    existing_inst = provisioning_fixture["existing_inst"]
    headers = provisioning_fixture["admin_headers"]

    # Assign an active rector directly
    rector_role = (
        await db_session.execute(select(Role).where(Role.name == SystemRole.RECTOR.value))
    ).scalar_one()
    rector_user = User(
        email="rector.activo@existente.edu.co",
        username="rector_activo",
        hashed_password=password_hasher.hash("RectorActivo2026*!"),
        first_name="Rector",
        last_name="Activo",
        document_type=DocumentType.CC,
        document_number="88776655",
        institution_id=existing_inst.id,
        is_active=True,
        is_verified=True,
    )
    db_session.add(rector_user)
    await db_session.flush()

    db_session.add(
        UserRole(
            user_id=rector_user.id,
            role_id=rector_role.id,
            institution_id=existing_inst.id,
            is_active=True,
        )
    )
    await db_session.commit()

    # Attempt to invite another rector
    invite_payload = {
        "first_name": "Segundo",
        "last_name": "Rector",
        "document_type": "CC",
        "document_number": "11223344",
        "email": "segundo.rector@existente.edu.co",
    }
    res = await client.post(
        f"/api/v1/institutions/{existing_inst.id}/rector-invitation",
        json=invite_payload,
        headers=headers,
    )
    assert res.status_code == 409
    data = res.json()
    assert data["error"]["code"] == "RECTOR_ALREADY_EXISTS"


async def test_verify_invitation_public_endpoint(
    client: AsyncClient,
    provisioning_fixture: dict[str, Any],
) -> None:
    """Verify that public verification endpoint validates raw token and masks email."""
    existing_inst = provisioning_fixture["existing_inst"]
    headers = provisioning_fixture["admin_headers"]

    # Issue invitation
    invite_payload = {
        "first_name": "Beatriz",
        "last_name": "Pinzón",
        "document_type": "CC",
        "document_number": "52998877",
        "email": "betty.rectora@sanjose.edu.co",
    }
    res_inv = await client.post(
        f"/api/v1/institutions/{existing_inst.id}/rector-invitation",
        json=invite_payload,
        headers=headers,
    )
    raw_token = res_inv.json()["raw_invitation_token"]

    # Verify token
    res_ver = await client.post(
        "/api/v1/auth/verify-invitation",
        json={"token": raw_token},
    )
    assert res_ver.status_code == 200
    data = res_ver.json()
    assert data["valid"] is True
    assert data["first_name"] == "Beatriz"
    assert data["institution_name"] == existing_inst.name
    assert "@" in data["email"]
    assert "***" in data["email"]  # Masked email


async def test_accept_invitation_lifecycle_argon2_and_role_activation(
    client: AsyncClient,
    provisioning_fixture: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    """Verify full end-to-end acceptance: setting Argon2id password and activating account."""
    existing_inst = provisioning_fixture["existing_inst"]
    headers = provisioning_fixture["admin_headers"]

    # 1. National Admin invites Rector
    invite_payload = {
        "first_name": "Aura",
        "last_name": "María",
        "document_type": "CC",
        "document_number": "60112233",
        "email": "auramaria@sanjose.edu.co",
    }
    res_inv = await client.post(
        f"/api/v1/institutions/{existing_inst.id}/rector-invitation",
        json=invite_payload,
        headers=headers,
    )
    raw_token = res_inv.json()["raw_invitation_token"]

    # 2. Rector submits password
    accept_payload = {
        "token": raw_token,
        "password": "PasswordSegura2026*!",
        "password_confirmation": "PasswordSegura2026*!",
    }
    res_acc = await client.post(
        "/api/v1/auth/accept-invitation",
        json=accept_payload,
    )
    assert res_acc.status_code == 200
    acc_data = res_acc.json()
    assert acc_data["is_active"] is True
    user_id = uuid.UUID(acc_data["user_id"])

    # 3. Verify in database: User is active, verified, password hashed with Argon2id
    user_stmt = select(User).where(User.id == user_id)
    user_db = (await db_session.execute(user_stmt)).scalar_one()
    assert user_db.is_active is True
    assert user_db.is_verified is True
    assert password_hasher.verify("PasswordSegura2026*!", user_db.hashed_password) is True

    # 4. Verify UserRole is active for Rector
    ur_stmt = select(UserRole).where(UserRole.user_id == user_id)
    ur_db = (await db_session.execute(ur_stmt)).scalar_one()
    assert ur_db.is_active is True
    assert ur_db.institution_id == existing_inst.id


async def test_accept_invitation_replay_attack_rejected(
    client: AsyncClient,
    provisioning_fixture: dict[str, Any],
) -> None:
    """Verify that a redeemed invitation token cannot be reused (replay prevention)."""
    existing_inst = provisioning_fixture["existing_inst"]
    headers = provisioning_fixture["admin_headers"]

    # Issue invitation
    res_inv = await client.post(
        f"/api/v1/institutions/{existing_inst.id}/rector-invitation",
        json={
            "first_name": "Hermes",
            "last_name": "Pinzón",
            "document_type": "CC",
            "document_number": "70112233",
            "email": "hermes@sanjose.edu.co",
        },
        headers=headers,
    )
    raw_token = res_inv.json()["raw_invitation_token"]

    # First redemption -> Success
    res_first = await client.post(
        "/api/v1/auth/accept-invitation",
        json={
            "token": raw_token,
            "password": "PasswordHermes2026*!",
            "password_confirmation": "PasswordHermes2026*!",
        },
    )
    assert res_first.status_code == 200

    # Second redemption with same token -> Rejection (409 Conflict)
    res_second = await client.post(
        "/api/v1/auth/accept-invitation",
        json={
            "token": raw_token,
            "password": "PasswordHermes2026*!",
            "password_confirmation": "PasswordHermes2026*!",
        },
    )
    assert res_second.status_code == 409
    assert res_second.json()["error"]["code"] == "INVITATION_ALREADY_USED"


async def test_accept_invitation_invalid_token_rejected(
    client: AsyncClient,
) -> None:
    """Verify that random or invalid tokens return 404."""
    res = await client.post(
        "/api/v1/auth/accept-invitation",
        json={
            "token": "token_completamente_falso_y_aleatorio_1234567890",
            "password": "PasswordValida2026*!",
            "password_confirmation": "PasswordValida2026*!",
        },
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "INVITATION_NOT_FOUND"


async def test_accept_invitation_expired_token_rejected(
    client: AsyncClient,
    provisioning_fixture: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    """Verify that an expired invitation token returns 410 Gone / INVITATION_EXPIRED."""
    existing_inst = provisioning_fixture["existing_inst"]
    headers = provisioning_fixture["admin_headers"]

    # Issue invitation
    res_inv = await client.post(
        f"/api/v1/institutions/{existing_inst.id}/rector-invitation",
        json={
            "first_name": "Inés",
            "last_name": "Ramírez",
            "document_type": "CC",
            "document_number": "41002233",
            "email": "ines@sanjose.edu.co",
        },
        headers=headers,
    )
    raw_token = res_inv.json()["raw_invitation_token"]
    inv_id = uuid.UUID(res_inv.json()["invitation_id"])

    # Force expiration in database
    await db_session.execute(
        select(RectorInvitation).where(RectorInvitation.id == inv_id)
    )
    from sqlalchemy import update
    await db_session.execute(
        update(RectorInvitation)
        .where(RectorInvitation.id == inv_id)
        .values(expires_at=datetime.now(UTC) - timedelta(hours=1))
    )
    await db_session.commit()

    # Attempt to accept expired invitation -> 410
    res_acc = await client.post(
        "/api/v1/auth/accept-invitation",
        json={
            "token": raw_token,
            "password": "PasswordInes2026*!",
            "password_confirmation": "PasswordInes2026*!",
        },
    )
    assert res_acc.status_code == 410
    assert res_acc.json()["error"]["code"] == "INVITATION_EXPIRED"


async def test_onboarded_rector_immediate_academic_access_without_403(
    client: AsyncClient,
    provisioning_fixture: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    """Verify full E2E flow: National Admin provisions institution -> invites rector -> rector activates -> rector accesses institutional endpoints."""
    mun = provisioning_fixture["municipality"]
    admin_headers = provisioning_fixture["admin_headers"]

    # 1. National Admin creates a new institution
    inst_payload = {
        "dane_code": "111001099901",
        "name": "Institución Educativa Departamental El Dorado",
        "email": "contacto@eldorado.edu.co",
        "municipality_id": str(mun.id),
        "main_campus_name": "Sede Principal El Dorado",
    }
    res_inst = await client.post("/api/v1/institutions", json=inst_payload, headers=admin_headers)
    assert res_inst.status_code == 201
    inst_id = res_inst.json()["id"]

    # 2. National Admin invites Rector
    invite_payload = {
        "first_name": "Rodrigo",
        "last_name": "Díaz",
        "document_type": "CC",
        "document_number": "79112233",
        "email": "rector@eldorado.edu.co",
    }
    res_inv = await client.post(
        f"/api/v1/institutions/{inst_id}/rector-invitation",
        json=invite_payload,
        headers=admin_headers,
    )
    assert res_inv.status_code == 201
    raw_token = res_inv.json()["raw_invitation_token"]

    # 3. Rector accepts invitation
    res_acc = await client.post(
        "/api/v1/auth/accept-invitation",
        json={
            "token": raw_token,
            "password": "PasswordRector2026*!",
            "password_confirmation": "PasswordRector2026*!",
        },
    )
    assert res_acc.status_code == 200
    rector_user_id = res_acc.json()["user_id"]

    # 4. Rector logs in
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": "rector@eldorado.edu.co", "password": "PasswordRector2026*!"},
    )
    assert login_res.status_code == 200
    rector_token = login_res.json()["access_token"]
    rector_headers = {"Authorization": f"Bearer {rector_token}"}

    # 5. Rector accesses /api/v1/institutions/me -> 200 OK without 403 context error!
    me_res = await client.get("/api/v1/institutions/me", headers=rector_headers)
    assert me_res.status_code == 200
    assert me_res.json()["id"] == inst_id
    assert me_res.json()["name"] == "Institución Educativa Departamental El Dorado"

    # 6. Rector accesses /api/v1/academic-years -> 200 OK (empty list, no 403!)
    ay_res = await client.get("/api/v1/academic-years", headers=rector_headers)
    assert ay_res.status_code == 200
    assert ay_res.json()["total"] == 0


async def test_provision_institution_with_dane_municipality_code_success(
    client: AsyncClient,
    provisioning_fixture: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    """TEST A: Provision institution using 5-digit DANE municipality code (e.g. 68081)."""
    headers = provisioning_fixture["admin_headers"]

    # Seed official catalog record for LIC NUEVA GENERACION in Santander/Barrancabermeja (68081)
    from app.models.official_catalog import OfficialInstitutionCatalog, OfficialCampusCatalog
    cat_inst = OfficialInstitutionCatalog(
        dane_code="368081003201",
        name="LIC NUEVA GENERACION",
        department_code="68",
        department_name="SANTANDER",
        municipality_code="68081",
        municipality_name="BARRANCABERMEJA",
        sector="OFICIAL",
        status="ACTIVO",
    )
    db_session.add(cat_inst)
    await db_session.flush()

    cat_campus = OfficialCampusCatalog(
        official_institution_id=cat_inst.id,
        dane_sede_code="368081003201",
        name="LIC NUEVA GENERACION - SEDE PRINCIPAL",
        is_main=True,
        zone="URBANA",
        status="ACTIVA",
        is_active=True,
    )
    db_session.add(cat_campus)
    await db_session.commit()

    payload = {
        "dane_code": "368081003201",
        "name": "LIC NUEVA GENERACION",
        "email": "rectoria@nuevageneracion.edu.co",
        "phone": "+57 607 6220000",
        "address": "Calle 50 # 15-20",
        "municipality_id": "68081",  # 5-digit DANE code sent by frontend
        "main_campus_name": "Sede Principal",
    }

    res = await client.post("/api/v1/institutions", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["dane_code"] == "368081003201"
    assert data["name"] == "LIC NUEVA GENERACION"
    assert data["is_active"] is True
    # Verify that municipality_id in response is a valid UUID
    assert uuid.UUID(data["municipality_id"])
    assert len(data["campuses"]) >= 1


async def test_provision_institution_duplicate_dane_code_rejected(
    client: AsyncClient,
    provisioning_fixture: dict[str, Any],
) -> None:
    """TEST B: Provisioning duplicate institution DANE code returns 409 Conflict."""
    headers = provisioning_fixture["admin_headers"]
    mun = provisioning_fixture["municipality"]

    # 1. Provision once with valid municipality UUID
    payload1 = {
        "dane_code": "111001007777",
        "name": "INSTITUTO SAN JUAN ORIGINAL",
        "email": "original@sanjuan.edu.co",
        "municipality_id": str(mun.id),
    }
    res1 = await client.post("/api/v1/institutions", json=payload1, headers=headers)
    assert res1.status_code == 201

    # 2. Attempt duplicate provisioning with same DANE code
    payload2 = {
        "dane_code": "111001007777",
        "name": "INSTITUTO SAN JUAN DUPLICADO",
        "email": "duplicado@sanjuan.edu.co",
        "municipality_id": str(mun.id),
    }
    res2 = await client.post("/api/v1/institutions", json=payload2, headers=headers)
    assert res2.status_code == 409
    data = res2.json()
    assert data["error"]["code"] == "DUPLICATE_DANE_CODE"


async def test_provision_institution_invalid_municipality_code_rejected(
    client: AsyncClient,
    provisioning_fixture: dict[str, Any],
) -> None:
    """TEST C: Unresolvable municipality code returns 404 MUNICIPALITY_NOT_FOUND."""
    headers = provisioning_fixture["admin_headers"]

    payload = {
        "dane_code": "111001008888",
        "name": "COLEGIO CON MUNICIPIO INEXISTENTE",
        "email": "contacto@inexistente.edu.co",
        "municipality_id": "99999",  # Invalid unresolvable DANE code
    }

    res = await client.post("/api/v1/institutions", json=payload, headers=headers)
    assert res.status_code == 404
    data = res.json()
    assert data["error"]["code"] == "MUNICIPALITY_NOT_FOUND"


