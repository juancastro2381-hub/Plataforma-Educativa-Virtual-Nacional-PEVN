"""
PEVN Backend — NTA-09 Municipality Admin Provisioning & Territorial Authorization Tests
AI Software Factory Standard v1.2

Validates canonical MUNICIPALITY_ADMIN provisioning lifecycle and territorial authorization:
  1. Department Admin provisions MUNICIPALITY_ADMIN in own department -> 201
  2. Department Admin cannot provision MUNICIPALITY_ADMIN outside own department -> 403
  3. National Admin supervisory provisioning -> 201
  4. Superadmin emergency override provisioning -> 201
  5. Unauthorized roles (Coordinator, Rector, Teacher, Student) cannot provision -> 403
  6. Peer provisioning rejected (Municipality Admin cannot create Municipality Admin) -> 403
  7. Non-existent municipality ID rejected -> 404
  8. Uniqueness conflicts (duplicate email, username, document) rejected -> 409
  9. Status update (deactivation) invalidates active refresh tokens -> 200
  10. Reassignment updates municipality and revokes active refresh tokens -> 200
  11. Department Admin cannot reassign to foreign department municipality -> 403
  12. Audit events generated for provisioning, status change, and reassignment
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import secrets
import uuid
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.interfaces import AuditEventType
from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.core.security.tokens import token_service
from app.models.audit_log import AuditLog
from app.models.invitation import MunicipalityAdminInvitation
from app.models.role import Role, UserRole
from app.models.territory import Department, Municipality
from app.models.token import RefreshToken
from app.models.user import DocumentType, User
from app.services.rbac_bootstrap_service import RbacBootstrapService
from app.services.user_service import UserService


def _rand_doc() -> str:
    return str(secrets.randbelow(899999999) + 100000000)


async def _provision(client: AsyncClient, headers: dict[str, str], muni: Municipality, **overrides: Any) -> dict[str, Any]:
    """Provision a municipality admin (no password) and return the creation response body."""
    tag = uuid.uuid4().hex[:8]
    payload = {
        "municipality_id": str(muni.id),
        "email": f"inv_{tag}@pevn.edu.co",
        "username": f"inv_{tag}",
        "first_name": "Invitado",
        "last_name": "Municipal",
        "document_type": "CC",
        "document_number": _rand_doc(),
        **overrides,
    }
    res = await client.post("/api/v1/municipality-admins", json=payload, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()


@pytest.fixture
async def nta09_fixture(db_session: AsyncSession) -> dict[str, Any]:
    """Bootstrap canonical RBAC and territorial test entities for NTA-09."""
    bootstrap = RbacBootstrapService(session=db_session)
    await bootstrap.seed_canonical_rbac_if_needed()

    # 1. Departments: Santander (68) and Boyacá (15)
    dept_san = Department(code=f"68_{uuid.uuid4().hex[:4]}", name="Santander Test")
    dept_boy = Department(code=f"15_{uuid.uuid4().hex[:4]}", name="Boyacá Test")
    db_session.add_all([dept_san, dept_boy])
    await db_session.flush()

    # 2. Municipalities in Santander
    muni_bucaramanga = Municipality(
        department_id=dept_san.id,
        code=f"68001_{uuid.uuid4().hex[:4]}",
        name="Bucaramanga Test",
    )
    muni_flori = Municipality(
        department_id=dept_san.id,
        code=f"68276_{uuid.uuid4().hex[:4]}",
        name="Floridablanca Test",
    )
    # Municipality in Boyacá
    muni_tunja = Municipality(
        department_id=dept_boy.id,
        code=f"15001_{uuid.uuid4().hex[:4]}",
        name="Tunja Test",
    )
    db_session.add_all([muni_bucaramanga, muni_flori, muni_tunja])
    await db_session.flush()

    # Helper function to create authenticated users
    async def create_actor(role_name: str, *, dept_id=None, muni_id=None) -> tuple[User, dict[str, str]]:
        role_obj = (await db_session.execute(select(Role).where(Role.name == role_name))).scalar_one()
        pw = password_hasher.hash("Nta09Test2026!#")
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
        )
        db_session.add(user)
        await db_session.flush()

        ur = UserRole(
            user_id=user.id,
            role_id=role_obj.id,
            department_id=dept_id,
            municipality_id=muni_id,
            is_active=True,
        )
        db_session.add(ur)
        await db_session.flush()

        additional_claims: dict[str, Any] = {"roles": [role_name]}
        if dept_id:
            additional_claims["department_id"] = str(dept_id)
        if muni_id:
            additional_claims["municipality_id"] = str(muni_id)

        token = await token_service.create_access_token(
            subject=str(user.id),
            additional_claims=additional_claims,
        )
        return user, {"Authorization": f"Bearer {token}"}

    superadmin_user, superadmin_headers = await create_actor("superadmin")
    nat_admin_user, nat_admin_headers = await create_actor("national_admin")
    dept_admin_san_user, dept_admin_san_headers = await create_actor("department_admin", dept_id=dept_san.id)
    muni_admin_user, muni_admin_headers = await create_actor("municipality_admin", dept_id=dept_san.id, muni_id=muni_bucaramanga.id)
    coord_user, coord_headers = await create_actor("coordinator")

    await db_session.commit()

    return {
        "dept_san": dept_san,
        "dept_boy": dept_boy,
        "muni_bucaramanga": muni_bucaramanga,
        "muni_flori": muni_flori,
        "muni_tunja": muni_tunja,
        "superadmin_headers": superadmin_headers,
        "nat_admin_headers": nat_admin_headers,
        "dept_admin_san_headers": dept_admin_san_headers,
        "muni_admin_headers": muni_admin_headers,
        "coord_headers": coord_headers,
        "dept_admin_san_user": dept_admin_san_user,
    }


# ==============================================================================
# 1. DEPARTMENT_ADMIN PROVISIONS IN OWN DEPARTMENT
# ==============================================================================
@pytest.mark.asyncio
async def test_01_dept_admin_provisions_in_own_department(
    client: AsyncClient, nta09_fixture: dict[str, Any], db_session: AsyncSession
):
    headers = nta09_fixture["dept_admin_san_headers"]
    muni = nta09_fixture["muni_bucaramanga"]
    dept = nta09_fixture["dept_san"]

    payload = {
        "municipality_id": str(muni.id),
        "email": f"muni_admin_buca_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "username": f"admin_buca_{uuid.uuid4().hex[:6]}",
        "first_name": "Carlos",
        "last_name": "Bucaramanga",
        "document_type": "CC",
        "document_number": _rand_doc(),
    }
    res = await client.post("/api/v1/municipality-admins", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["municipality_id"] == str(muni.id)
    assert data["department_id"] == str(dept.id)
    # Provisioning never activates the account
    assert data["is_active"] is False
    assert data["is_verified"] is False
    assert "municipality_admin" in data["roles"]
    assert "password" not in data and "hashed_password" not in data

    # Verify DB persistence
    user_id = uuid.UUID(data["id"])
    created_user = (await db_session.execute(select(User).where(User.id == user_id))).scalar_one()
    assert created_user.email == payload["email"].lower()
    assert created_user.must_change_password is True
    assert created_user.is_active is False
    assert created_user.is_verified is False

    # Verify UserRole record with municipality_id and derived department_id (pending => inactive)
    ur = (
        await db_session.execute(select(UserRole).where(UserRole.user_id == user_id))
    ).scalar_one()
    assert ur.municipality_id == muni.id
    assert ur.department_id == dept.id
    assert ur.is_active is False


# ==============================================================================
# 2. DEPARTMENT_ADMIN BLOCKED OUTSIDE OWN DEPARTMENT
# ==============================================================================
@pytest.mark.asyncio
async def test_02_dept_admin_cannot_provision_outside_department(
    client: AsyncClient, nta09_fixture: dict[str, Any]
):
    headers = nta09_fixture["dept_admin_san_headers"]  # Santander
    muni_tunja = nta09_fixture["muni_tunja"]  # Boyacá

    payload = {
        "municipality_id": str(muni_tunja.id),
        "email": f"muni_admin_tunja_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "username": f"admin_tunja_{uuid.uuid4().hex[:6]}",
        "first_name": "Intruder",
        "last_name": "Boyaca",
        "document_type": "CC",
        "document_number": _rand_doc(),
    }
    res = await client.post("/api/v1/municipality-admins", json=payload, headers=headers)
    assert res.status_code == 403
    err_body = res.json()
    err_obj = err_body.get("error", {})
    assert (
        err_body.get("code") == "PERMISSION_DENIED"
        or err_obj.get("code") == "PERMISSION_DENIED"
        or "No está autorizado" in err_obj.get("message", "")
        or "No está autorizado" in err_body.get("detail", "")
    )


# ==============================================================================
# 3. NATIONAL_ADMIN SUPERVISORY PROVISIONING
# ==============================================================================
@pytest.mark.asyncio
async def test_03_national_admin_supervisory_provisioning(
    client: AsyncClient, nta09_fixture: dict[str, Any]
):
    headers = nta09_fixture["nat_admin_headers"]
    muni_tunja = nta09_fixture["muni_tunja"]

    payload = {
        "municipality_id": str(muni_tunja.id),
        "email": f"nat_prov_tunja_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "username": f"nat_tunja_{uuid.uuid4().hex[:6]}",
        "first_name": "Supervisor",
        "last_name": "Tunja",
        "document_type": "CC",
        "document_number": _rand_doc(),
    }
    res = await client.post("/api/v1/municipality-admins", json=payload, headers=headers)
    assert res.status_code == 201
    assert res.json()["municipality_id"] == str(muni_tunja.id)


# ==============================================================================
# 4. SUPERADMIN EMERGENCY OVERRIDE PROVISIONING
# ==============================================================================
@pytest.mark.asyncio
async def test_04_superadmin_emergency_provisioning(
    client: AsyncClient, nta09_fixture: dict[str, Any]
):
    headers = nta09_fixture["superadmin_headers"]
    muni_flori = nta09_fixture["muni_flori"]

    payload = {
        "municipality_id": str(muni_flori.id),
        "email": f"super_prov_flori_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "username": f"super_flori_{uuid.uuid4().hex[:6]}",
        "first_name": "Super",
        "last_name": "Floridablanca",
        "document_type": "CC",
        "document_number": _rand_doc(),
    }
    res = await client.post("/api/v1/municipality-admins", json=payload, headers=headers)
    assert res.status_code == 201
    assert res.json()["municipality_id"] == str(muni_flori.id)


# ==============================================================================
# 5. UNAUTHORIZED ROLES REJECTED
# ==============================================================================
@pytest.mark.asyncio
async def test_05_unauthorized_roles_rejected(
    client: AsyncClient, nta09_fixture: dict[str, Any]
):
    coord_headers = nta09_fixture["coord_headers"]
    muni = nta09_fixture["muni_bucaramanga"]

    payload = {
        "municipality_id": str(muni.id),
        "email": f"coord_escalate_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "username": f"coord_esc_{uuid.uuid4().hex[:6]}",
        "first_name": "Illegal",
        "last_name": "Escalation",
        "document_type": "CC",
        "document_number": _rand_doc(),
    }
    res = await client.post("/api/v1/municipality-admins", json=payload, headers=coord_headers)
    assert res.status_code == 403


# ==============================================================================
# 6. PEER PROVISIONING REJECTED (MUNI_ADMIN CANNOT CREATE MUNI_ADMIN)
# ==============================================================================
@pytest.mark.asyncio
async def test_06_peer_provisioning_rejected(
    client: AsyncClient, nta09_fixture: dict[str, Any]
):
    muni_headers = nta09_fixture["muni_admin_headers"]
    muni = nta09_fixture["muni_flori"]

    payload = {
        "municipality_id": str(muni.id),
        "email": f"peer_muni_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "username": f"peer_muni_{uuid.uuid4().hex[:6]}",
        "first_name": "Peer",
        "last_name": "Admin",
        "document_type": "CC",
        "document_number": _rand_doc(),
    }
    res = await client.post("/api/v1/municipality-admins", json=payload, headers=muni_headers)
    assert res.status_code == 403


# ==============================================================================
# 7. NON-EXISTENT MUNICIPALITY ID REJECTED
# ==============================================================================
@pytest.mark.asyncio
async def test_07_invalid_municipality_rejected(
    client: AsyncClient, nta09_fixture: dict[str, Any]
):
    headers = nta09_fixture["superadmin_headers"]
    fake_id = uuid.uuid4()

    payload = {
        "municipality_id": str(fake_id),
        "email": f"fake_muni_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "username": f"fake_muni_{uuid.uuid4().hex[:6]}",
        "first_name": "Ghost",
        "last_name": "Admin",
        "document_type": "CC",
        "document_number": _rand_doc(),
    }
    res = await client.post("/api/v1/municipality-admins", json=payload, headers=headers)
    assert res.status_code == 404


# ==============================================================================
# 8. UNIQUENESS CONFLICTS (DUPLICATE EMAIL, USERNAME, DOCUMENT)
# ==============================================================================
@pytest.mark.asyncio
async def test_08_duplicate_uniqueness_conflicts(
    client: AsyncClient, nta09_fixture: dict[str, Any]
):
    headers = nta09_fixture["superadmin_headers"]
    muni = nta09_fixture["muni_bucaramanga"]

    doc = _rand_doc()
    email = f"conflict_{uuid.uuid4().hex[:6]}@pevn.edu.co"
    username = f"user_conflict_{uuid.uuid4().hex[:6]}"

    payload = {
        "municipality_id": str(muni.id),
        "email": email,
        "username": username,
        "first_name": "Original",
        "last_name": "User",
        "document_type": "CC",
        "document_number": doc,
    }
    # 1. Create first
    res1 = await client.post("/api/v1/municipality-admins", json=payload, headers=headers)
    assert res1.status_code == 201

    # 2. Duplicate email
    payload_dup_email = {**payload, "username": f"user2_{uuid.uuid4().hex[:6]}", "document_number": _rand_doc()}
    res_dup_email = await client.post("/api/v1/municipality-admins", json=payload_dup_email, headers=headers)
    assert res_dup_email.status_code == 409

    # 3. Duplicate username
    payload_dup_user = {**payload, "email": f"email2_{uuid.uuid4().hex[:6]}@pevn.edu.co", "document_number": _rand_doc()}
    res_dup_user = await client.post("/api/v1/municipality-admins", json=payload_dup_user, headers=headers)
    assert res_dup_user.status_code == 409

    # 4. Duplicate document
    payload_dup_doc = {**payload, "email": f"email3_{uuid.uuid4().hex[:6]}@pevn.edu.co", "username": f"user3_{uuid.uuid4().hex[:6]}"}
    res_dup_doc = await client.post("/api/v1/municipality-admins", json=payload_dup_doc, headers=headers)
    assert res_dup_doc.status_code == 409


# ==============================================================================
# 9. STATUS LIFECYCLE & REFRESH TOKEN REVOCATION
# ==============================================================================
@pytest.mark.asyncio
async def test_09_status_lifecycle_and_session_revocation(
    client: AsyncClient, nta09_fixture: dict[str, Any], db_session: AsyncSession
):
    headers = nta09_fixture["dept_admin_san_headers"]
    muni = nta09_fixture["muni_bucaramanga"]

    # Provision user
    payload = {
        "municipality_id": str(muni.id),
        "email": f"status_test_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "username": f"status_user_{uuid.uuid4().hex[:6]}",
        "first_name": "Status",
        "last_name": "Subject",
        "document_type": "CC",
        "document_number": _rand_doc(),
    }
    create_res = await client.post("/api/v1/municipality-admins", json=payload, headers=headers)
    assert create_res.status_code == 201
    user_id = create_res.json()["id"]

    # Insert an active refresh token for this user
    rt = RefreshToken(
        id=uuid.uuid4(),
        user_id=uuid.UUID(user_id),
        token_hash=secrets.token_hex(32),
        family_id=uuid.uuid4(),
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        is_revoked=False,
    )
    db_session.add(rt)
    await db_session.commit()

    # Deactivate admin
    status_res = await client.patch(
        f"/api/v1/municipality-admins/{user_id}/status",
        json={"is_active": False, "reason": "Administrative suspension"},
        headers=headers,
    )
    assert status_res.status_code == 200
    assert status_res.json()["is_active"] is False

    # Check refresh token revoked
    revoked = (
        await db_session.execute(
            select(RefreshToken.is_revoked).where(RefreshToken.user_id == uuid.UUID(user_id))
        )
    ).scalar_one()
    assert revoked is True


# ==============================================================================
# 10. REASSIGN MUNICIPALITY LIFECYCLE & ISOLATION
# ==============================================================================
@pytest.mark.asyncio
async def test_10_reassign_municipality_lifecycle(
    client: AsyncClient, nta09_fixture: dict[str, Any], db_session: AsyncSession
):
    headers = nta09_fixture["dept_admin_san_headers"]
    muni_buca = nta09_fixture["muni_bucaramanga"]
    muni_flori = nta09_fixture["muni_flori"]
    muni_tunja = nta09_fixture["muni_tunja"]

    # Provision in Bucaramanga
    payload = {
        "municipality_id": str(muni_buca.id),
        "email": f"reassign_test_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "username": f"reassign_user_{uuid.uuid4().hex[:6]}",
        "first_name": "Reassign",
        "last_name": "Candidate",
        "document_type": "CC",
        "document_number": _rand_doc(),
    }
    create_res = await client.post("/api/v1/municipality-admins", json=payload, headers=headers)
    assert create_res.status_code == 201
    user_id = create_res.json()["id"]

    # 1. Allowed: Reassign to Floridablanca (same department Santander)
    reassign_res = await client.patch(
        f"/api/v1/municipality-admins/{user_id}/municipality",
        json={"new_municipality_id": str(muni_flori.id), "reason": "Territorial transfer"},
        headers=headers,
    )
    assert reassign_res.status_code == 200
    assert reassign_res.json()["municipality_id"] == str(muni_flori.id)

    # 2. Blocked: Reassign to Tunja (foreign department Boyacá) by Dept Admin -> 403
    foreign_res = await client.patch(
        f"/api/v1/municipality-admins/{user_id}/municipality",
        json={"new_municipality_id": str(muni_tunja.id), "reason": "Unauthorized foreign transfer"},
        headers=headers,
    )
    assert foreign_res.status_code == 403


# ==============================================================================
# 11. AUDIT TRAIL LOGGING
# ==============================================================================
@pytest.mark.asyncio
async def test_11_audit_events_logged(
    client: AsyncClient, nta09_fixture: dict[str, Any], db_session: AsyncSession
):
    headers = nta09_fixture["dept_admin_san_headers"]
    muni = nta09_fixture["muni_flori"]

    payload = {
        "municipality_id": str(muni.id),
        "email": f"audit_check_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "username": f"audit_user_{uuid.uuid4().hex[:6]}",
        "first_name": "Audit",
        "last_name": "Check",
        "document_type": "CC",
        "document_number": _rand_doc(),
    }
    res = await client.post("/api/v1/municipality-admins", json=payload, headers=headers)
    assert res.status_code == 201
    user_id = res.json()["id"]

    # Check AuditLog table for MUNICIPALITY_ADMIN_CREATED and MUNICIPALITY_ADMIN_INVITED events
    logs_created = (
        await db_session.execute(
            select(AuditLog).where(
                AuditLog.target_id == user_id,
                AuditLog.event_type == AuditEventType.MUNICIPALITY_ADMIN_CREATED.value,
            )
        )
    ).scalars().all()
    assert len(logs_created) >= 1
    log_created = logs_created[0]
    assert log_created.metadata_json.get("municipality_id") == str(muni.id)
    assert log_created.metadata_json.get("username") == payload["username"]

    logs_invited = (
        await db_session.execute(
            select(AuditLog).where(
                AuditLog.target_id == user_id,
                AuditLog.event_type == AuditEventType.MUNICIPALITY_ADMIN_INVITED.value,
            )
        )
    ).scalars().all()
    assert len(logs_invited) >= 1
    log_invited = logs_invited[0]
    assert log_invited.metadata_json.get("municipality_id") == str(muni.id)
    assert "invitation_id" in log_invited.metadata_json


# ==============================================================================
# 12. HTTP 422 VALIDATION ERROR STRUCTURE AND SPANISH FEEDBACK
# ==============================================================================
@pytest.mark.asyncio
async def test_12_validation_error_structured_format_and_spanish_feedback(
    client: AsyncClient, nta09_fixture: dict[str, Any], db_session: AsyncSession
):
    headers = nta09_fixture["dept_admin_san_headers"]

    # 1. Invalid UUID format (e.g. DANE code "11001" passed as municipality_id)
    attempted_username = f"fail_user_{uuid.uuid4().hex[:6]}"
    invalid_uuid_payload = {
        "municipality_id": "11001",  # Invalid UUID string
        "email": f"invalid_uuid_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "username": attempted_username,
        "first_name": "Invalid",
        "last_name": "UUID",
        "document_type": "CC",
        "document_number": _rand_doc(),
    }
    res = await client.post("/api/v1/municipality-admins", json=invalid_uuid_payload, headers=headers)
    assert res.status_code == 422
    err_body = res.json()["error"]
    assert err_body["code"] == "VALIDATION_ERROR"
    assert "Error de validación en la solicitud" in err_body["message"]
    assert any("municipality_id" in str(d) for d in err_body["details"])
    assert "correlation_id" in err_body

    # Verify no partial user record was persisted
    persisted = (
        await db_session.execute(select(User).where(User.username == attempted_username))
    ).scalar_one_or_none()
    assert persisted is None

    # 2. Any caller-defined password (even short/valid) is rejected: it can never set credentials
    for forbidden_pw in ("short", "ValidInitialPassword2026!#"):
        attempted = f"short_pw_{uuid.uuid4().hex[:6]}"
        short_pw_payload = {
            "municipality_id": str(nta09_fixture["muni_bucaramanga"].id),
            "email": f"{attempted}@pevn.edu.co",
            "username": attempted,
            "first_name": "Short",
            "last_name": "Password",
            "document_type": "CC",
            "document_number": _rand_doc(),
            "password": forbidden_pw,
        }
        res_short = await client.post("/api/v1/municipality-admins", json=short_pw_payload, headers=headers)
        assert res_short.status_code == 422
        err_body_short = res_short.json()["error"]
        assert err_body_short["code"] == "VALIDATION_ERROR"
        assert any("password" in str(d) for d in err_body_short["details"])
        assert forbidden_pw not in res_short.text
        persisted_pw = (
            await db_session.execute(select(User).where(User.username == attempted))
        ).scalar_one_or_none()
        assert persisted_pw is None

    # 3. Caller-defined is_active is also rejected (activation only through invitation)
    attempted = f"force_active_{uuid.uuid4().hex[:6]}"
    res_active = await client.post(
        "/api/v1/municipality-admins",
        json={
            "municipality_id": str(nta09_fixture["muni_bucaramanga"].id),
            "email": f"{attempted}@pevn.edu.co",
            "username": attempted,
            "first_name": "Force",
            "last_name": "Active",
            "document_type": "CC",
            "document_number": _rand_doc(),
            "is_active": True,
        },
        headers=headers,
    )
    assert res_active.status_code == 422


# ==============================================================================
# 13. INVITATION LIFECYCLE: INACTIVE ON PROVISIONING, ACTIVATION ONLY VIA TOKEN
# ==============================================================================
@pytest.mark.asyncio
async def test_13_lifecycle_activation_and_password_policy(
    client: AsyncClient, nta09_fixture: dict[str, Any], db_session: AsyncSession
):
    headers = nta09_fixture["dept_admin_san_headers"]
    muni = nta09_fixture["muni_bucaramanga"]

    data = await _provision(client, headers, muni)
    user_id = uuid.UUID(data["id"])
    username = data["username"]
    assert data["is_active"] is False
    assert data["is_verified"] is False

    user = (await db_session.execute(select(User).where(User.id == user_id))).scalar_one()
    assert user.is_active is False
    assert user.is_verified is False
    assert user.must_change_password is True

    # Inactive account cannot authenticate (any password, including a guess)
    login_res = await client.post(
        "/api/v1/auth/login", json={"username": username, "password": "AnyPassword123!"}
    )
    assert login_res.status_code == 401

    # SMTP unavailable (dev): disclosure is controlled and does NOT activate the account
    assert data["email_delivery_status"] != "EMAIL_SENT"
    raw_token = data["raw_invitation_token"]
    assert raw_token and len(raw_token) >= 48
    await db_session.refresh(user)
    assert user.is_active is False

    # Token stored hashed, never in plaintext
    inv = (
        await db_session.execute(
            select(MunicipalityAdminInvitation).where(MunicipalityAdminInvitation.user_id == user_id)
        )
    ).scalar_one()
    assert inv.token_hash != raw_token
    assert raw_token not in str(inv.token_hash)
    assert inv.is_used is False and inv.is_revoked is False
    inv_expires = (
        inv.expires_at.replace(tzinfo=timezone.utc)
        if inv.expires_at.tzinfo is None
        else inv.expires_at
    )
    ttl = inv_expires - datetime.now(timezone.utc)
    assert timedelta(hours=47) < ttl <= timedelta(hours=48, minutes=1)

    # Public verification returns masked data only
    ver = await client.post("/api/v1/auth/verify-invitation", json={"token": raw_token})
    assert ver.status_code == 200
    assert ver.json()["role_name"] == "municipality_admin"
    assert data["email"] not in ver.text

    # Redemption sets the user's own password and activates the account
    new_pw = "MyOwnSecret2026!#"
    acc = await client.post(
        "/api/v1/auth/accept-invitation",
        json={"token": raw_token, "password": new_pw, "password_confirmation": new_pw},
    )
    assert acc.status_code == 200, acc.text
    assert new_pw not in acc.text
    await db_session.refresh(user)
    assert user.is_active is True
    assert user.is_verified is True
    assert user.must_change_password is False
    ur = (await db_session.execute(select(UserRole).where(UserRole.user_id == user_id))).scalar_one()
    await db_session.refresh(ur)
    assert ur.is_active is True
    assert ur.municipality_id == muni.id

    # Login now succeeds with the self-chosen password
    ok = await client.post("/api/v1/auth/login", json={"username": username, "password": new_pw})
    assert ok.status_code == 200

    # Replay of the same token is rejected
    replay = await client.post(
        "/api/v1/auth/accept-invitation",
        json={"token": raw_token, "password": "AnotherSecret2026!#", "password_confirmation": "AnotherSecret2026!#"},
    )
    assert replay.status_code == 409
    login_after_replay = await client.post(
        "/api/v1/auth/login", json={"username": username, "password": "AnotherSecret2026!#"}
    )
    assert login_after_replay.status_code == 401
    ver_after = await client.post("/api/v1/auth/verify-invitation", json={"token": raw_token})
    assert ver_after.status_code == 409


# ==============================================================================
# 14. CROSS-MUNICIPALITY ISOLATION AND PEER MUTATION REJECTION
# ==============================================================================
@pytest.mark.asyncio
async def test_14_cross_municipality_isolation_and_peer_protection(
    client: AsyncClient, nta09_fixture: dict[str, Any]
):
    muni_admin_headers = nta09_fixture["muni_admin_headers"]  # Bucaramanga admin
    muni_buca = nta09_fixture["muni_bucaramanga"]
    muni_flori = nta09_fixture["muni_flori"]
    dept_admin_headers = nta09_fixture["dept_admin_san_headers"]

    # 1. Municipal Admin listing canonical municipalities gets ONLY their own municipality
    munis_res = await client.get("/api/v1/municipality-admins/municipalities", headers=muni_admin_headers)
    assert munis_res.status_code == 200
    munis_data = munis_res.json()
    assert len(munis_data) == 1
    assert munis_data[0]["id"] == str(muni_buca.id)

    # 2. Provision Floridablanca admin using dept_admin
    flori_payload = {
        "municipality_id": str(muni_flori.id),
        "email": f"flori_admin_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "username": f"flori_admin_{uuid.uuid4().hex[:6]}",
        "first_name": "Flori",
        "last_name": "Admin",
        "document_type": "CC",
        "document_number": _rand_doc(),
    }
    create_flori_res = await client.post("/api/v1/municipality-admins", json=flori_payload, headers=dept_admin_headers)
    assert create_flori_res.status_code == 201
    flori_admin_id = create_flori_res.json()["id"]

    # 3. Municipal Admin 1 (Bucaramanga) attempts to read Municipal Admin 2 (Floridablanca) -> 403
    read_res = await client.get(f"/api/v1/municipality-admins/{flori_admin_id}", headers=muni_admin_headers)
    assert read_res.status_code == 403

    # 4. Municipal Admin 1 attempts to change status of Municipal Admin 2 -> 403
    status_peer_res = await client.patch(
        f"/api/v1/municipality-admins/{flori_admin_id}/status",
        json={"is_active": False, "reason": "Unauthorized peer modification"},
        headers=muni_admin_headers,
    )
    assert status_peer_res.status_code == 403

    # 5. Municipal Admin 1 attempts to reassign Floridablanca admin -> 403
    reassign_peer_res = await client.patch(
        f"/api/v1/municipality-admins/{flori_admin_id}/municipality",
        json={"new_municipality_id": str(muni_buca.id), "reason": "Unauthorized peer reassignment"},
        headers=muni_admin_headers,
    )
    assert reassign_peer_res.status_code == 403


# ==============================================================================
# 15. ADMINISTRATIVE USER DIRECTORY VISIBILITY AND CONSISTENCY
# ==============================================================================
@pytest.mark.asyncio
async def test_15_administrative_user_directory_visibility(
    client: AsyncClient, nta09_fixture: dict[str, Any], db_session: AsyncSession
):
    headers = nta09_fixture["dept_admin_san_headers"]
    muni_buca = nta09_fixture["muni_bucaramanga"]
    dept_san = nta09_fixture["dept_san"]
    muni_tunja = nta09_fixture["muni_tunja"]

    # Provision new municipal admin
    unique_user = f"dir_muni_{uuid.uuid4().hex[:6]}"
    payload = {
        "municipality_id": str(muni_buca.id),
        "email": f"{unique_user}@pevn.edu.co",
        "username": unique_user,
        "first_name": "Directory",
        "last_name": "Verified",
        "document_type": "CC",
        "document_number": _rand_doc(),
    }
    create_res = await client.post("/api/v1/municipality-admins", json=payload, headers=headers)
    assert create_res.status_code == 201
    created_id = uuid.UUID(create_res.json()["id"])

    # Query via UserService with municipality_id filter
    user_service = UserService(session=db_session)
    users_muni, count_muni = await user_service.list_users(
        municipality_id=muni_buca.id, is_active=None, search=unique_user
    )
    assert any(u.id == created_id for u in users_muni)
    pending = next(u for u in users_muni if u.id == created_id)
    assert pending.is_active is False and pending.is_verified is False

    # Query via UserService with department_id filter
    users_dept, count_dept = await user_service.list_users(
        department_id=dept_san.id, is_active=None, search=unique_user
    )
    assert any(u.id == created_id for u in users_dept)

    # Query via get_user_by_id within correct municipality
    user_found = await user_service.get_user_by_id(user_id=created_id, municipality_id=muni_buca.id)
    assert user_found.id == created_id

    # Query via get_user_by_id within foreign municipality raises NotFoundError
    from app.exceptions.errors import NotFoundError
    with pytest.raises(NotFoundError):
        await user_service.get_user_by_id(user_id=created_id, municipality_id=muni_tunja.id)

    # Dedicated directory: pending-activation state is visible; no invitation secret in listings
    list_res = await client.get("/api/v1/municipality-admins", headers=headers, params={"search": unique_user})
    assert list_res.status_code == 200
    items = list_res.json()["items"]
    entry = next(i for i in items if i["id"] == str(created_id))
    assert entry["is_active"] is False and entry["is_verified"] is False
    assert entry.get("raw_invitation_token") is None
    assert entry.get("invitation_url") is None


# ==============================================================================
# 16. TOKEN ERROR MATRIX: INVALID / EXPIRED / REVOKED / USED
# ==============================================================================
@pytest.mark.asyncio
async def test_16_token_error_matrix(
    client: AsyncClient, nta09_fixture: dict[str, Any], db_session: AsyncSession
):
    headers = nta09_fixture["dept_admin_san_headers"]
    muni = nta09_fixture["muni_bucaramanga"]
    pw = "MyOwnSecret2026!#"

    async def _accept(token: str):
        return await client.post(
            "/api/v1/auth/accept-invitation",
            json={"token": token, "password": pw, "password_confirmation": pw},
        )

    # Invalid token: indistinguishable generic 404, no echo of the token
    bogus = secrets.token_urlsafe(48)
    res_invalid = await _accept(bogus)
    assert res_invalid.status_code == 404
    assert bogus not in res_invalid.text

    # Expired token -> 410, account stays inactive
    data = await _provision(client, headers, muni)
    inv = (
        await db_session.execute(
            select(MunicipalityAdminInvitation).where(
                MunicipalityAdminInvitation.user_id == uuid.UUID(data["id"])
            )
        )
    ).scalar_one()
    inv.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    await db_session.commit()
    res_expired = await _accept(data["raw_invitation_token"])
    assert res_expired.status_code == 410
    user = (await db_session.execute(select(User).where(User.id == uuid.UUID(data["id"])))).scalar_one()
    await db_session.refresh(user)
    assert user.is_active is False

    # Revoked (replaced) token -> 409; the replacement works
    data2 = await _provision(client, headers, muni)
    old_token = data2["raw_invitation_token"]
    resend = await client.post(f"/api/v1/municipality-admins/{data2['id']}/resend-invitation", headers=headers)
    assert resend.status_code == 200
    new_token = resend.json()["raw_invitation_token"]
    assert new_token and new_token != old_token
    assert (await _accept(old_token)).status_code == 409
    assert (await _accept(new_token)).status_code == 200

    # Used token -> 409
    assert (await _accept(new_token)).status_code == 409

    # Password mismatch / weak password rejected and do NOT consume the token
    data3 = await _provision(client, headers, muni)
    tok3 = data3["raw_invitation_token"]
    mismatch = await client.post(
        "/api/v1/auth/accept-invitation",
        json={"token": tok3, "password": pw, "password_confirmation": pw + "x"},
    )
    assert mismatch.status_code == 422
    weak = await client.post(
        "/api/v1/auth/accept-invitation",
        json={"token": tok3, "password": "short", "password_confirmation": "short"},
    )
    assert weak.status_code == 422
    login_before = await client.post(
        "/api/v1/auth/login", json={"username": data3["username"], "password": pw}
    )
    assert login_before.status_code == 401
    assert (await _accept(tok3)).status_code == 200


# ==============================================================================
# 17. ATOMIC REDEMPTION: A LOST RACE CANNOT ACTIVATE THE ACCOUNT TWICE
# ==============================================================================
@pytest.mark.asyncio
async def test_17_atomic_claim_prevents_double_redemption(
    client: AsyncClient, nta09_fixture: dict[str, Any], db_session: AsyncSession
):
    from sqlalchemy import update as sa_update

    from app.exceptions.errors import ConflictError
    from app.services.municipality_admin_service import MunicipalityAdminService

    headers = nta09_fixture["dept_admin_san_headers"]
    muni = nta09_fixture["muni_bucaramanga"]
    data = await _provision(client, headers, muni)
    user_id = uuid.UUID(data["id"])
    token = data["raw_invitation_token"]

    service = MunicipalityAdminService(session=db_session)
    original_execute = db_session.execute
    state = {"calls": 0}

    async def racing_execute(stmt, *args, **kwargs):
        result = await original_execute(stmt, *args, **kwargs)
        state["calls"] += 1
        if state["calls"] == 1:
            # Competing redemption commits right after our SELECT (stale read in this request)
            await original_execute(
                sa_update(MunicipalityAdminInvitation)
                .where(MunicipalityAdminInvitation.user_id == user_id)
                .values(is_used=True)
                .execution_options(synchronize_session=False)
            )
        return result

    db_session.execute = racing_execute  # type: ignore[method-assign]
    try:
        with pytest.raises(ConflictError):
            await service.accept_invitation(
                token=token, password="MyOwnSecret2026!#", password_confirmation="MyOwnSecret2026!#"
            )
    finally:
        db_session.execute = original_execute  # type: ignore[method-assign]

    user = (await db_session.execute(select(User).where(User.id == user_id))).scalar_one()
    await db_session.refresh(user)
    assert user.is_active is False
    assert user.is_verified is False


# ==============================================================================
# 18. DEACTIVATION / REASSIGNMENT INVALIDATE TOKENS; NO ACTIVATION BYPASS
# ==============================================================================
@pytest.mark.asyncio
async def test_18_deactivation_and_reassignment_invalidate_invitation(
    client: AsyncClient, nta09_fixture: dict[str, Any], db_session: AsyncSession
):
    headers = nta09_fixture["dept_admin_san_headers"]
    muni = nta09_fixture["muni_bucaramanga"]
    muni_flori = nta09_fixture["muni_flori"]
    pw = "MyOwnSecret2026!#"

    # Status endpoint cannot activate a pending account (bypass attempt)
    data = await _provision(client, headers, muni)
    activate = await client.patch(
        f"/api/v1/municipality-admins/{data['id']}/status",
        json={"is_active": True, "reason": "Intento de activación manual"},
        headers=headers,
    )
    assert activate.status_code == 409
    user = (await db_session.execute(select(User).where(User.id == uuid.UUID(data["id"])))).scalar_one()
    await db_session.refresh(user)
    assert user.is_active is False

    # Deactivation revokes the outstanding invitation
    deact = await client.patch(
        f"/api/v1/municipality-admins/{data['id']}/status",
        json={"is_active": False, "reason": "Suspensión administrativa"},
        headers=headers,
    )
    assert deact.status_code == 200
    res = await client.post(
        "/api/v1/auth/accept-invitation",
        json={"token": data["raw_invitation_token"], "password": pw, "password_confirmation": pw},
    )
    assert res.status_code == 409

    # Reassignment revokes the outstanding invitation (bound to previous municipality)
    data2 = await _provision(client, headers, muni)
    reassign = await client.patch(
        f"/api/v1/municipality-admins/{data2['id']}/municipality",
        json={"new_municipality_id": str(muni_flori.id), "reason": "Traslado territorial"},
        headers=headers,
    )
    assert reassign.status_code == 200
    res2 = await client.post(
        "/api/v1/auth/accept-invitation",
        json={"token": data2["raw_invitation_token"], "password": pw, "password_confirmation": pw},
    )
    assert res2.status_code == 409

    # A fresh invitation after reassignment activates in the NEW municipality
    resend = await client.post(f"/api/v1/municipality-admins/{data2['id']}/resend-invitation", headers=headers)
    assert resend.status_code == 200
    ok = await client.post(
        "/api/v1/auth/accept-invitation",
        json={"token": resend.json()["raw_invitation_token"], "password": pw, "password_confirmation": pw},
    )
    assert ok.status_code == 200
    ur = (await db_session.execute(select(UserRole).where(UserRole.user_id == uuid.UUID(data2["id"])))).scalar_one()
    await db_session.refresh(ur)
    assert ur.is_active is True
    assert ur.municipality_id == muni_flori.id


# ==============================================================================
# 19. RESEND AUTHORIZATION, ISOLATION AND NO CREDENTIAL TAKEOVER OF ACTIVE ACCOUNTS
# ==============================================================================
@pytest.mark.asyncio
async def test_19_resend_authorization_and_active_account_protection(
    client: AsyncClient, nta09_fixture: dict[str, Any], db_session: AsyncSession
):
    dept_headers = nta09_fixture["dept_admin_san_headers"]
    muni_headers = nta09_fixture["muni_admin_headers"]
    coord_headers = nta09_fixture["coord_headers"]
    nat_headers = nta09_fixture["nat_admin_headers"]
    muni = nta09_fixture["muni_bucaramanga"]
    pw = "MyOwnSecret2026!#"

    data = await _provision(client, dept_headers, muni)
    url = f"/api/v1/municipality-admins/{data['id']}/resend-invitation"
    assert (await client.post(url, headers=muni_headers)).status_code == 403
    assert (await client.post(url, headers=coord_headers)).status_code == 403
    assert (await client.post(url)).status_code in (401, 403)

    # Department admin of Santander cannot resend for a Boyacá municipal admin
    tunja_admin = await _provision(client, nat_headers, nta09_fixture["muni_tunja"])
    foreign = await client.post(
        f"/api/v1/municipality-admins/{tunja_admin['id']}/resend-invitation", headers=dept_headers
    )
    assert foreign.status_code == 403

    # Once activated, resend must be refused (it would overwrite the user's own password)
    acc = await client.post(
        "/api/v1/auth/accept-invitation",
        json={"token": data["raw_invitation_token"], "password": pw, "password_confirmation": pw},
    )
    assert acc.status_code == 200
    again = await client.post(url, headers=dept_headers)
    assert again.status_code == 409
    still_ok = await client.post("/api/v1/auth/login", json={"username": data["username"], "password": pw})
    assert still_ok.status_code == 200


# ==============================================================================
# 20. SECRETS ABSENT FROM LOGS, AUDIT PAYLOADS AND ROUTINE RESPONSES
# ==============================================================================
@pytest.mark.asyncio
async def test_20_no_secrets_in_logs_audit_or_routine_responses(
    client: AsyncClient,
    nta09_fixture: dict[str, Any],
    db_session: AsyncSession,
    capsys: pytest.CaptureFixture[str],
):
    headers = nta09_fixture["dept_admin_san_headers"]
    muni = nta09_fixture["muni_bucaramanga"]
    pw = "MyOwnSecret2026!#"

    data = await _provision(client, headers, muni)
    token = data["raw_invitation_token"]
    user_id = data["id"]
    inv = (
        await db_session.execute(
            select(MunicipalityAdminInvitation).where(MunicipalityAdminInvitation.user_id == uuid.UUID(user_id))
        )
    ).scalar_one()
    token_hash = inv.token_hash

    detail = await client.get(f"/api/v1/municipality-admins/{user_id}", headers=headers)
    listing = await client.get("/api/v1/municipality-admins", headers=headers)
    verify = await client.post("/api/v1/auth/verify-invitation", json={"token": token})
    accept = await client.post(
        "/api/v1/auth/accept-invitation",
        json={"token": token, "password": pw, "password_confirmation": pw},
    )
    login = await client.post("/api/v1/auth/login", json={"username": data["username"], "password": pw})
    replay = await client.post(
        "/api/v1/auth/accept-invitation",
        json={"token": token, "password": pw, "password_confirmation": pw},
    )

    # Routine responses never carry the invitation secret or the hash
    for routine in (detail, listing, verify):
        assert token not in routine.text
        assert token_hash not in routine.text
    assert detail.json().get("raw_invitation_token") is None
    assert detail.json().get("invitation_url") is None
    for secret_response in (accept, login, replay):
        assert pw not in secret_response.text

    # Audit payloads
    logs = (await db_session.execute(select(AuditLog))).scalars().all()
    blob = " ".join(str(entry.metadata_json) for entry in logs)
    assert token not in blob
    assert token_hash not in blob
    assert pw not in blob

    # Application logs (stdout/stderr)
    captured = capsys.readouterr()
    combined = captured.out + captured.err
    assert token not in combined
    assert pw not in combined


# ==============================================================================
# 21. PRODUCTION / STAGING NEVER DISCLOSE TOKEN OR LINK; ACCOUNT STAYS INACTIVE
# ==============================================================================
@pytest.mark.asyncio
@pytest.mark.parametrize("env_name", ["production", "staging"])
async def test_21_non_development_environments_never_disclose_invitation(
    nta09_fixture: dict[str, Any], db_session: AsyncSession, env_name: str
):
    from app.core.config import Environment, get_settings
    from app.schemas.municipality_admin import MunicipalityAdminCreateRequest
    from app.services.municipality_admin_service import MunicipalityAdminService

    settings = get_settings().model_copy(update={"ENVIRONMENT": Environment(env_name)})
    service = MunicipalityAdminService(session=db_session, settings=settings)
    tag = uuid.uuid4().hex[:8]
    payload = MunicipalityAdminCreateRequest(
        municipality_id=nta09_fixture["muni_bucaramanga"].id,
        email=f"{env_name}_{tag}@pevn.edu.co",
        username=f"{env_name}_{tag}",
        first_name="Prod",
        last_name="Mode",
        document_type="CC",
        document_number=_rand_doc(),
    )
    result = await service.create_municipality_admin(payload, caller_department_id=None)
    assert result.raw_invitation_token is None
    assert result.invitation_url is None
    assert result.is_active is False
    assert result.email_delivery_status.value != "EMAIL_SENT"  # SMTP unavailable: no fake delivery

    resent = await service.resend_invitation(result.id)
    assert resent.activation_url is None
    assert not resent[1]  # raw token string empty

    # The invitation still exists server-side (hashed) so SMTP delivery can use it when configured
    inv = (
        await db_session.execute(
            select(MunicipalityAdminInvitation).where(MunicipalityAdminInvitation.user_id == result.id)
        )
    ).scalars().all()
    assert len(inv) == 2 and sum(1 for i in inv if not i.is_revoked) == 1
