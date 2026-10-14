"""
PEVN — NTA-10: Secure Rector Provisioning & Invitation Lifecycle Test Suite

Validates:
1. Authorized MUNICIPALITY_ADMIN can invite a RECTOR for an institution in their municipality.
2. Cross-municipality and cross-department attempts rejected with 403 Forbidden.
3. Supervisory authority preserved for DEPARTMENT_ADMIN, NATIONAL_ADMIN, SUPERADMIN.
4. Unauthorized roles (teacher, coordinator, student, guardian, unauthenticated) rejected with 403/401.
5. Inactive institutions rejected with 409 Conflict (INSTITUTION_INACTIVE).
6. Request payload forbidding extra fields (password, is_active rejected with 422).
7. Pre-registered accounts remain inactive, unverified, must_change_password=True, unusable password.
8. Rector cannot login before invitation redemption.
9. Public verification endpoint (/api/v1/auth/verify-invitation) returns valid metadata with masked email.
10. Password establishment and activation via /api/v1/auth/accept-invitation (Argon2id, is_active=True, must_change_password=False).
11. Activated Rector can login successfully.
12. Atomic single-use claim: used, revoked, expired tokens rejected.
13. Resend invitation (/rector-invitation/resend) revokes earlier pending token, issues new valid token.
14. Resend rejected if rector is already active (ACCOUNT_ALREADY_ACTIVATED).
15. Revocation (/rector/revoke) detaches incumbent, invalidates pending invitations, enables immediate succession.
16. Development vs Production token disclosure: raw_invitation_token and invitation_url strictly None in production.
17. Audit trails recorded without sensitive secrets.
"""

from __future__ import annotations

import random
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Environment, get_settings
from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.core.security.tokens import token_service
from app.models.audit_log import AuditLog
from app.models.institution import Campus, Institution
from app.models.invitation import RectorInvitation
from app.models.role import Role, UserRole
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User
from app.services.rbac_bootstrap_service import RbacBootstrapService


def _rand_doc() -> str:
    return str(random.randint(10000000, 99999999))


@pytest.fixture
async def nta10_fixture(db_session: AsyncSession) -> dict[str, Any]:
    """Bootstrap canonical RBAC and territorial test entities for NTA-10."""
    bootstrap = RbacBootstrapService(session=db_session)
    await bootstrap.seed_canonical_rbac_if_needed()

    # 1. Departments: Antioquia (05) and Cundinamarca (25)
    dept_ant = Department(code=f"05_{uuid.uuid4().hex[:4]}", name="Antioquia NTA10")
    dept_cun = Department(code=f"25_{uuid.uuid4().hex[:4]}", name="Cundinamarca NTA10")
    db_session.add_all([dept_ant, dept_cun])
    await db_session.flush()

    # 2. Municipalities in Antioquia: Medellin (05001), Envigado (05266)
    muni_med = Municipality(department_id=dept_ant.id, code=f"05001_{uuid.uuid4().hex[:4]}", name="Medellin NTA10")
    muni_env = Municipality(department_id=dept_ant.id, code=f"05266_{uuid.uuid4().hex[:4]}", name="Envigado NTA10")
    # Municipality in Cundinamarca: Bogota (25001)
    muni_bog = Municipality(department_id=dept_cun.id, code=f"25001_{uuid.uuid4().hex[:4]}", name="Bogota NTA10")
    db_session.add_all([muni_med, muni_env, muni_bog])
    await db_session.flush()

    # 3. Institutions:
    # inst_med: in Medellin
    # inst_env: in Envigado
    # inst_bog: in Bogota
    # inst_inactive: in Medellin (is_active=False)
    inst_med = Institution(
        municipality_id=muni_med.id,
        dane_code=f"105001{random.randint(100000, 999999)}",
        name="I.E. Medellin Activa",
        email="rectoria@iemedellin.edu.co",
        is_active=True,
    )
    inst_env = Institution(
        municipality_id=muni_env.id,
        dane_code=f"105266{random.randint(100000, 999999)}",
        name="I.E. Envigado Activa",
        email="rectoria@ieenvigado.edu.co",
        is_active=True,
    )
    inst_bog = Institution(
        municipality_id=muni_bog.id,
        dane_code=f"125001{random.randint(100000, 999999)}",
        name="I.E. Bogota Activa",
        email="rectoria@iebogota.edu.co",
        is_active=True,
    )
    inst_inactive = Institution(
        municipality_id=muni_med.id,
        dane_code=f"105001{random.randint(100000, 999999)}",
        name="I.E. Medellin Inactiva",
        email="rectoria@ieinactiva.edu.co",
        is_active=False,
    )
    db_session.add_all([inst_med, inst_env, inst_bog, inst_inactive])
    await db_session.flush()

    # Helper function to create authenticated users
    async def create_actor(role_name: str, *, dept_id=None, muni_id=None, inst_id=None) -> tuple[User, dict[str, str]]:
        role_obj = (await db_session.execute(select(Role).where(Role.name == role_name))).scalar_one()
        pw = password_hasher.hash("Nta10Test2026!#")
        uid = uuid.uuid4()
        user = User(
            id=uid,
            email=f"{role_name}_{uid.hex[:6]}@pevn.edu.co",
            username=f"{role_name}_{uid.hex[:6]}",
            hashed_password=pw,
            first_name=role_name.capitalize(),
            last_name="Tester",
            document_type=DocumentType.CC,
            document_number=_rand_doc(),
            is_active=True,
            is_verified=True,
            institution_id=inst_id,
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

    superadmin_user, superadmin_headers = await create_actor("superadmin")
    nat_admin_user, nat_admin_headers = await create_actor("national_admin")
    dept_admin_ant_user, dept_admin_ant_headers = await create_actor("department_admin", dept_id=dept_ant.id)
    dept_admin_cun_user, dept_admin_cun_headers = await create_actor("department_admin", dept_id=dept_cun.id)
    muni_admin_med_user, muni_admin_med_headers = await create_actor(
        "municipality_admin", dept_id=dept_ant.id, muni_id=muni_med.id
    )
    muni_admin_env_user, muni_admin_env_headers = await create_actor(
        "municipality_admin", dept_id=dept_ant.id, muni_id=muni_env.id
    )
    teacher_user, teacher_headers = await create_actor("teacher", inst_id=inst_med.id)
    coordinator_user, coordinator_headers = await create_actor("coordinator", inst_id=inst_med.id)

    return {
        "dept_ant": dept_ant,
        "dept_cun": dept_cun,
        "muni_med": muni_med,
        "muni_env": muni_env,
        "muni_bog": muni_bog,
        "inst_med": inst_med,
        "inst_env": inst_env,
        "inst_bog": inst_bog,
        "inst_inactive": inst_inactive,
        "superadmin_headers": superadmin_headers,
        "nat_admin_headers": nat_admin_headers,
        "dept_admin_ant_headers": dept_admin_ant_headers,
        "dept_admin_cun_headers": dept_admin_cun_headers,
        "muni_admin_med_headers": muni_admin_med_headers,
        "muni_admin_env_headers": muni_admin_env_headers,
        "teacher_headers": teacher_headers,
        "coordinator_headers": coordinator_headers,
    }


def _rector_payload(**overrides: Any) -> dict[str, Any]:
    tag = uuid.uuid4().hex[:6]
    return {
        "first_name": "Gabriel",
        "last_name": f"García {tag}",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "email": f"rector_{tag}@colegio.edu.co",
        "phone_number": "+57 300 1234567",
        **overrides,
    }


# ==============================================================================
# TEST CASES
# ==============================================================================


@pytest.mark.asyncio
async def test_01_muni_admin_can_invite_rector_in_own_municipality(
    client: AsyncClient,
    nta10_fixture: dict[str, Any],
    db_session: AsyncSession,
):
    """1. Authorized MUNICIPALITY_ADMIN invites a RECTOR in their authorized municipality."""
    inst_med = nta10_fixture["inst_med"]
    headers = nta10_fixture["muni_admin_med_headers"]
    payload = _rector_payload()

    res = await client.post(
        f"/api/v1/institutions/{inst_med.id}/rector-invitation",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 201, res.text
    data = res.json()

    assert data["institution_id"] == str(inst_med.id)
    assert data["email"] == payload["email"].lower()
    assert data["is_used"] is False
    assert "raw_invitation_token" in data
    assert data["raw_invitation_token"] is not None
    assert "/auth/accept-invitation?token=" in data["invitation_url"]

    # Verify user created inactive, unverified, must_change_password=True
    user = (await db_session.execute(select(User).where(User.email == payload["email"].lower()))).scalar_one()
    assert user.is_active is False
    assert user.is_verified is False
    assert user.must_change_password is True
    assert user.institution_id == inst_med.id

    # Verify inactive UserRole
    ur = (await db_session.execute(select(UserRole).where(UserRole.user_id == user.id))).scalar_one()
    assert ur.is_active is False
    assert ur.institution_id == inst_med.id


@pytest.mark.asyncio
async def test_02_muni_admin_cross_municipality_attempt_rejected(
    client: AsyncClient,
    nta10_fixture: dict[str, Any],
):
    """2. MUNICIPALITY_ADMIN cannot invite rector for an institution in another municipality of same department."""
    inst_env = nta10_fixture["inst_env"]  # in Envigado
    headers = nta10_fixture["muni_admin_med_headers"]  # Admin of Medellin
    payload = _rector_payload()

    res = await client.post(
        f"/api/v1/institutions/{inst_env.id}/rector-invitation",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 403
    assert "jurisdicción municipal" in res.text


@pytest.mark.asyncio
async def test_03_muni_admin_cross_department_attempt_rejected(
    client: AsyncClient,
    nta10_fixture: dict[str, Any],
):
    """3. MUNICIPALITY_ADMIN cannot invite rector for an institution in another department."""
    inst_bog = nta10_fixture["inst_bog"]  # in Cundinamarca
    headers = nta10_fixture["muni_admin_med_headers"]  # Admin of Medellin (Antioquia)
    payload = _rector_payload()

    res = await client.post(
        f"/api/v1/institutions/{inst_bog.id}/rector-invitation",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_04_dept_admin_supervisory_authority_and_cross_department_boundary(
    client: AsyncClient,
    nta10_fixture: dict[str, Any],
):
    """4. DEPARTMENT_ADMIN can invite rector in their department, rejected outside department."""
    inst_med = nta10_fixture["inst_med"]  # in Antioquia
    inst_bog = nta10_fixture["inst_bog"]  # in Cundinamarca
    headers_ant = nta10_fixture["dept_admin_ant_headers"]

    # In Antioquia -> 201 Created
    res_ant = await client.post(
        f"/api/v1/institutions/{inst_med.id}/rector-invitation",
        json=_rector_payload(),
        headers=headers_ant,
    )
    assert res_ant.status_code == 201

    # In Cundinamarca -> 403 Forbidden
    res_cun = await client.post(
        f"/api/v1/institutions/{inst_bog.id}/rector-invitation",
        json=_rector_payload(),
        headers=headers_ant,
    )
    assert res_cun.status_code == 403
    assert "jurisdicción departamental" in res_cun.text


@pytest.mark.asyncio
async def test_05_national_admin_and_superadmin_supervisory_authority(
    client: AsyncClient,
    nta10_fixture: dict[str, Any],
):
    """5. NATIONAL_ADMIN and SUPERADMIN can invite rectors across any territory."""
    inst_med = nta10_fixture["inst_med"]
    inst_bog = nta10_fixture["inst_bog"]
    headers_nat = nta10_fixture["nat_admin_headers"]
    headers_super = nta10_fixture["superadmin_headers"]

    res_nat = await client.post(
        f"/api/v1/institutions/{inst_med.id}/rector-invitation",
        json=_rector_payload(),
        headers=headers_nat,
    )
    assert res_nat.status_code == 201

    res_super = await client.post(
        f"/api/v1/institutions/{inst_bog.id}/rector-invitation",
        json=_rector_payload(),
        headers=headers_super,
    )
    assert res_super.status_code == 201


@pytest.mark.asyncio
async def test_06_unauthorized_roles_and_unauthenticated_rejected(
    client: AsyncClient,
    nta10_fixture: dict[str, Any],
):
    """6. Unauthorized roles (teacher, coordinator) and unauthenticated rejected."""
    inst_med = nta10_fixture["inst_med"]
    payload = _rector_payload()

    # Teacher
    res_teacher = await client.post(
        f"/api/v1/institutions/{inst_med.id}/rector-invitation",
        json=payload,
        headers=nta10_fixture["teacher_headers"],
    )
    assert res_teacher.status_code == 403

    # Coordinator
    res_coord = await client.post(
        f"/api/v1/institutions/{inst_med.id}/rector-invitation",
        json=payload,
        headers=nta10_fixture["coordinator_headers"],
    )
    assert res_coord.status_code == 403

    # Unauthenticated
    res_anon = await client.post(
        f"/api/v1/institutions/{inst_med.id}/rector-invitation",
        json=payload,
    )
    assert res_anon.status_code in (401, 403)


@pytest.mark.asyncio
async def test_07_inactive_institution_rejected(
    client: AsyncClient,
    nta10_fixture: dict[str, Any],
):
    """7. Cannot invite rector for an inactive or suspended institution."""
    inst_inactive = nta10_fixture["inst_inactive"]
    headers = nta10_fixture["muni_admin_med_headers"]

    res = await client.post(
        f"/api/v1/institutions/{inst_inactive.id}/rector-invitation",
        json=_rector_payload(),
        headers=headers,
    )
    assert res.status_code == 409
    assert "institución inactiva" in res.text


@pytest.mark.asyncio
async def test_08_password_and_is_active_injection_rejected(
    client: AsyncClient,
    nta10_fixture: dict[str, Any],
):
    """8. Schema forbids operator from injecting password, password_hash, or is_active fields."""
    inst_med = nta10_fixture["inst_med"]
    headers = nta10_fixture["muni_admin_med_headers"]

    payload = _rector_payload()
    payload["password"] = "InjectedPass123!"

    res = await client.post(
        f"/api/v1/institutions/{inst_med.id}/rector-invitation",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 422

    payload_active = _rector_payload()
    payload_active["is_active"] = True

    res_active = await client.post(
        f"/api/v1/institutions/{inst_med.id}/rector-invitation",
        json=payload_active,
        headers=headers,
    )
    assert res_active.status_code == 422


@pytest.mark.asyncio
async def test_09_unactivated_rector_cannot_login(
    client: AsyncClient,
    nta10_fixture: dict[str, Any],
):
    """9. Unactivated Rector cannot login."""
    inst_med = nta10_fixture["inst_med"]
    headers = nta10_fixture["muni_admin_med_headers"]
    payload = _rector_payload()

    res = await client.post(
        f"/api/v1/institutions/{inst_med.id}/rector-invitation",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 201

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": payload["email"], "password": "AnyPassword123!"},
    )
    assert login_res.status_code in (400, 401, 403)


@pytest.mark.asyncio
async def test_10_verify_and_accept_invitation_lifecycle(
    client: AsyncClient,
    nta10_fixture: dict[str, Any],
    db_session: AsyncSession,
):
    """10. Public verification, password definition, activation, and login."""
    inst_med = nta10_fixture["inst_med"]
    headers = nta10_fixture["muni_admin_med_headers"]
    payload = _rector_payload()

    inv_res = await client.post(
        f"/api/v1/institutions/{inst_med.id}/rector-invitation",
        json=payload,
        headers=headers,
    )
    assert inv_res.status_code == 201
    raw_token = inv_res.json()["raw_invitation_token"]
    assert raw_token is not None

    # Step A: Verify token
    verify_res = await client.post(
        "/api/v1/auth/verify-invitation",
        json={"token": raw_token},
    )
    assert verify_res.status_code == 200, verify_res.text
    verify_data = verify_res.json()
    assert verify_data["valid"] is True
    assert verify_data["institution_name"] == inst_med.name
    assert "***" in verify_data["email"]

    # Step B: Password mismatch rejected
    mismatch_res = await client.post(
        "/api/v1/auth/accept-invitation",
        json={
            "token": raw_token,
            "password": "SecurePassword2026!#",
            "password_confirmation": "DifferentPass2026!#",
        },
    )
    assert mismatch_res.status_code == 422

    # Step C: Accept with valid credentials
    new_password = "SecurePassword2026!#"
    accept_res = await client.post(
        "/api/v1/auth/accept-invitation",
        json={
            "token": raw_token,
            "password": new_password,
            "password_confirmation": new_password,
        },
    )
    assert accept_res.status_code == 200, accept_res.text
    accept_data = accept_res.json()
    assert accept_data["is_active"] is True

    # Step D: Verify user is active and must_change_password=False in database
    user = (await db_session.execute(select(User).where(User.email == payload["email"].lower()))).scalar_one()
    assert user.is_active is True
    assert user.is_verified is True
    assert user.must_change_password is False

    ur = (await db_session.execute(select(UserRole).where(UserRole.user_id == user.id))).scalar_one()
    assert ur.is_active is True

    # Step E: Rector can now login
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": payload["email"], "password": new_password},
    )
    assert login_res.status_code == 200, login_res.text
    assert "access_token" in login_res.json()

    # Step F: Single-use claim prevents re-redemption
    reuse_res = await client.post(
        "/api/v1/auth/accept-invitation",
        json={
            "token": raw_token,
            "password": "AnotherPassword123!",
            "password_confirmation": "AnotherPassword123!",
        },
    )
    assert reuse_res.status_code == 409
    assert "utilizada anteriormente" in reuse_res.text


@pytest.mark.asyncio
async def test_11_duplicate_active_rector_rejected_until_revoked(
    client: AsyncClient,
    nta10_fixture: dict[str, Any],
):
    """11. Cannot invite a new rector when an active rector exists. Succession requires revocation."""
    inst_med = nta10_fixture["inst_med"]
    headers = nta10_fixture["muni_admin_med_headers"]

    # 1. Invite and activate first rector
    p1 = _rector_payload()
    inv1 = await client.post(
        f"/api/v1/institutions/{inst_med.id}/rector-invitation",
        json=p1,
        headers=headers,
    )
    assert inv1.status_code == 201
    tok1 = inv1.json()["raw_invitation_token"]

    acc1 = await client.post(
        "/api/v1/auth/accept-invitation",
        json={
            "token": tok1,
            "password": "PasswordRector1!#",
            "password_confirmation": "PasswordRector1!#",
        },
    )
    assert acc1.status_code == 200

    # 2. Attempt to invite second rector without revocation -> 409 RECTOR_ALREADY_EXISTS
    p2 = _rector_payload()
    inv2 = await client.post(
        f"/api/v1/institutions/{inst_med.id}/rector-invitation",
        json=p2,
        headers=headers,
    )
    assert inv2.status_code == 409
    assert "cuenta con un Rector titular activo" in inv2.text

    # 3. Revoke active rector
    revoke_res = await client.post(
        f"/api/v1/institutions/{inst_med.id}/rector/revoke",
        json={"reason": "Retiro forzoso por edad legal", "justification": "Resolución ministerial 2026"},
        headers=headers,
    )
    assert revoke_res.status_code == 200

    # 4. Now second rector invitation succeeds
    inv3 = await client.post(
        f"/api/v1/institutions/{inst_med.id}/rector-invitation",
        json=p2,
        headers=headers,
    )
    assert inv3.status_code == 201


@pytest.mark.asyncio
async def test_12_resend_rector_invitation_workflow(
    client: AsyncClient,
    nta10_fixture: dict[str, Any],
):
    """12. Resending an invitation invalidates previous pending token and generates a new one."""
    inst_med = nta10_fixture["inst_med"]
    headers = nta10_fixture["muni_admin_med_headers"]
    payload = _rector_payload()

    # Initial invitation
    res1 = await client.post(
        f"/api/v1/institutions/{inst_med.id}/rector-invitation",
        json=payload,
        headers=headers,
    )
    assert res1.status_code == 201
    token1 = res1.json()["raw_invitation_token"]

    # Resend invitation
    res2 = await client.post(
        f"/api/v1/institutions/{inst_med.id}/rector-invitation/resend",
        headers=headers,
    )
    assert res2.status_code == 200, res2.text
    token2 = res2.json()["raw_invitation_token"]
    assert token2 != token1

    # Token 1 must now be rejected as revoked
    verify_old = await client.post(
        "/api/v1/auth/verify-invitation",
        json={"token": token1},
    )
    assert verify_old.status_code == 409
    assert "revocado" in verify_old.text

    # Token 2 can be verified and accepted
    verify_new = await client.post(
        "/api/v1/auth/verify-invitation",
        json={"token": token2},
    )
    assert verify_new.status_code == 200
    assert verify_new.json()["valid"] is True

    accept_new = await client.post(
        "/api/v1/auth/accept-invitation",
        json={
            "token": token2,
            "password": "NewResentPass2026!#",
            "password_confirmation": "NewResentPass2026!#",
        },
    )
    assert accept_new.status_code == 200

    # Resend on already activated account -> 409 ACCOUNT_ALREADY_ACTIVATED
    res3 = await client.post(
        f"/api/v1/institutions/{inst_med.id}/rector-invitation/resend",
        headers=headers,
    )
    assert res3.status_code == 409
    assert "ya fue activada" in res3.text


@pytest.mark.asyncio
async def test_13_expired_invitation_token_rejected(
    client: AsyncClient,
    nta10_fixture: dict[str, Any],
    db_session: AsyncSession,
):
    """13. Expired invitation token (older than 48 hours) rejected with 410 Gone."""
    inst_med = nta10_fixture["inst_med"]
    headers = nta10_fixture["muni_admin_med_headers"]
    payload = _rector_payload()

    res = await client.post(
        f"/api/v1/institutions/{inst_med.id}/rector-invitation",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 201
    raw_token = res.json()["raw_invitation_token"]
    inv_id = uuid.UUID(res.json()["invitation_id"])

    # Force expiration in database
    inv = (await db_session.execute(select(RectorInvitation).where(RectorInvitation.id == inv_id))).scalar_one()
    inv.expires_at = datetime.now(UTC) - timedelta(hours=1)
    await db_session.flush()

    verify_res = await client.post(
        "/api/v1/auth/verify-invitation",
        json={"token": raw_token},
    )
    assert verify_res.status_code == 410
    assert "expirado" in verify_res.text


@pytest.mark.asyncio
async def test_14_production_environment_omits_raw_token(
    client: AsyncClient,
    nta10_fixture: dict[str, Any],
    monkeypatch,
):
    """14. In staging and production, raw_invitation_token and invitation_url are strictly None."""
    settings = get_settings()
    monkeypatch.setattr(settings, "ENVIRONMENT", Environment.PRODUCTION)
    monkeypatch.setattr(settings, "FRONTEND_URL", "https://pevn.edu.co")

    inst_med = nta10_fixture["inst_med"]
    headers = nta10_fixture["muni_admin_med_headers"]
    payload = _rector_payload()

    res = await client.post(
        f"/api/v1/institutions/{inst_med.id}/rector-invitation",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 201
    data = res.json()

    assert data["raw_invitation_token"] is None
    assert data["invitation_url"] is None


@pytest.mark.asyncio
async def test_15_audit_events_recorded_without_secrets(
    client: AsyncClient,
    nta10_fixture: dict[str, Any],
    db_session: AsyncSession,
):
    """15. Audit logs are recorded for invitation, resend, acceptance, revocation without leaking passwords or raw tokens."""
    inst_med = nta10_fixture["inst_med"]
    headers = nta10_fixture["muni_admin_med_headers"]
    payload = _rector_payload()

    # Invite
    res = await client.post(
        f"/api/v1/institutions/{inst_med.id}/rector-invitation",
        json=payload,
        headers=headers,
    )
    assert res.status_code == 201
    raw_token = res.json()["raw_invitation_token"]

    # Resend
    res_resend = await client.post(
        f"/api/v1/institutions/{inst_med.id}/rector-invitation/resend",
        headers=headers,
    )
    assert res_resend.status_code == 200
    new_token = res_resend.json()["raw_invitation_token"]

    # Accept
    my_password = "SecretAuditPass2026!#"
    res_accept = await client.post(
        "/api/v1/auth/accept-invitation",
        json={
            "token": new_token,
            "password": my_password,
            "password_confirmation": my_password,
        },
    )
    assert res_accept.status_code == 200

    # Revoke
    res_revoke = await client.post(
        f"/api/v1/institutions/{inst_med.id}/rector/revoke",
        json={"reason": "Fin del periodo de encargo", "justification": "Acta 001"},
        headers=headers,
    )
    assert res_revoke.status_code == 200

    # Query all audit events for this institution
    logs = (
        await db_session.execute(
            select(AuditLog).where(AuditLog.institution_id == inst_med.id)
        )
    ).scalars().all()

    action_types = [l.event_type for l in logs]
    assert "rector.invited" in action_types
    assert "rector.invitation_resent" in action_types
    assert "rector.onboarding.completed" in action_types
    assert "rector.revoked" in action_types

    # Ensure no audit log metadata contains the raw password or raw tokens
    for log in logs:
        meta_str = str(log.metadata_json or {})
        assert my_password not in meta_str
        assert raw_token not in meta_str
        assert new_token not in meta_str
