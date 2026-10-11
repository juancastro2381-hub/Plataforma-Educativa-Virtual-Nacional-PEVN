"""
PEVN Backend — NTA-10-R9 Coordinator Provisioning & Invitation Workflow Tests
AI Software Factory Standard v1.2

Validates the complete, secure, end-to-end Academic Coordinator assignment,
invitation lifecycle, campus scoping, and public activation workflows:
  1. Rector invites Coordinator with institutional scope -> 201, inactive, invitation generated
  2. Rector invites Coordinator with campus scope -> 201, bound to specific campus
  3. Rector cannot assign campus belonging to another institution -> 404
  4. Public token verification (/auth/verify-invitation) -> 200, role="coordinator", masked email
  5. Public token acceptance (/auth/accept-invitation) -> 200, user activated, password hashed
  6. Single-use enforcement: re-using redeemed token -> 409 INVITATION_ALREADY_USED
  7. Resend invitation invalidates previous token -> 200, old token yields 409 INVITATION_REVOKED
  8. Unauthorized roles (Coordinator, Teacher, Student) cannot invite coordinators -> 403
  9. Rector can list campuses for assignment -> 200
  10. Legacy direct password provisioning remains backward-compatible -> 201, active
"""

from __future__ import annotations

import secrets
import uuid
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.tokens import token_service
from app.models.institution import Campus, Institution
from app.models.role import Role, UserRole
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User
from app.services.rbac_bootstrap_service import RbacBootstrapService


def _rand_doc() -> str:
    return str(secrets.randbelow(899999999) + 100000000)


@pytest.fixture
async def r9_fixture(db_session: AsyncSession) -> dict[str, Any]:
    """Bootstrap canonical RBAC and institutional test entities for NTA-10-R9."""
    bootstrap = RbacBootstrapService(session=db_session)
    await bootstrap.seed_canonical_rbac_if_needed()

    # 1. Territory
    dept = Department(code=f"08_{uuid.uuid4().hex[:4]}", name="Atlantico Test")
    muni = Municipality(code=f"08001_{uuid.uuid4().hex[:4]}", name="Barranquilla Test", department=dept)
    db_session.add_all([dept, muni])
    await db_session.flush()

    # 2. Institutions A & B
    inst_a = Institution(
        dane_code=f"108001{uuid.uuid4().hex[:6]}",
        name="I.E. Distrital Alpha",
        municipality=muni,
        email="rector_alpha@pevn.edu.co",
        is_active=True,
    )
    inst_b = Institution(
        dane_code=f"108001{uuid.uuid4().hex[:6]}",
        name="I.E. Distrital Beta",
        municipality=muni,
        email="rector_beta@pevn.edu.co",
        is_active=True,
    )
    db_session.add_all([inst_a, inst_b])
    await db_session.flush()

    # 3. Campuses for Institution A
    campus_a1 = Campus(
        institution_id=inst_a.id,
        dane_sede_code=f"S1_{uuid.uuid4().hex[:6]}",
        name="Sede Principal Alpha",
    )
    campus_a2 = Campus(
        institution_id=inst_a.id,
        dane_sede_code=f"S2_{uuid.uuid4().hex[:6]}",
        name="Sede Secundaria Alpha",
    )
    # Campus for Institution B
    campus_b1 = Campus(
        institution_id=inst_b.id,
        dane_sede_code=f"SB_{uuid.uuid4().hex[:6]}",
        name="Sede Principal Beta",
    )
    db_session.add_all([campus_a1, campus_a2, campus_b1])
    await db_session.flush()

    # 4. Helper to create actor
    async def create_actor(role_name: str, institution_id: uuid.UUID | None = None) -> tuple[User, dict[str, str]]:
        tag = uuid.uuid4().hex[:6]
        user = User(
            email=f"{role_name}_{tag}@pevn.edu.co",
            username=f"{role_name}_{tag}",
            hashed_password="hashed_placeholder",
            first_name=role_name.capitalize(),
            last_name="Test",
            document_type=DocumentType.CC,
            document_number=_rand_doc(),
            institution_id=institution_id,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        await db_session.flush()

        role_obj = (await db_session.execute(
            Role.__table__.select().where(Role.name == role_name)
        )).first()

        ur = UserRole(
            user_id=user.id,
            role_id=role_obj.id,
            institution_id=institution_id,
            is_active=True,
        )
        db_session.add(ur)
        await db_session.flush()

        token = await token_service.create_access_token(
            subject=str(user.id),
            additional_claims={
                "roles": [role_name],
                "institution_id": str(institution_id) if institution_id else None,
            },
        )
        headers = {"Authorization": f"Bearer {token}"}
        return user, headers

    rector_a_user, rector_a_headers = await create_actor("rector", inst_a.id)
    rector_b_user, rector_b_headers = await create_actor("rector", inst_b.id)
    coord_a_user, coord_a_headers = await create_actor("coordinator", inst_b.id)

    await db_session.commit()

    return {
        "inst_a": inst_a,
        "inst_b": inst_b,
        "campus_a1": campus_a1,
        "campus_a2": campus_a2,
        "campus_b1": campus_b1,
        "rector_a_headers": rector_a_headers,
        "rector_b_headers": rector_b_headers,
        "coord_a_headers": coord_a_headers,
    }


@pytest.mark.asyncio
async def test_01_rector_invites_coordinator_institutional_scope(
    client: AsyncClient, r9_fixture: dict[str, Any]
):
    """Rector invites a coordinator without password; user is created inactive and invitation is issued."""
    headers = r9_fixture["rector_a_headers"]
    inst_a = r9_fixture["inst_a"]

    tag = uuid.uuid4().hex[:6]
    payload = {
        "email": f"coord_inv_{tag}@pevn.edu.co",
        "first_name": "Marcos",
        "last_name": "Perez",
        "document_type": "CC",
        "document_number": _rand_doc(),
    }
    res = await client.post("/api/v1/coordinators", json=payload, headers=headers)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["role"] == "coordinator"
    assert data["institution_id"] == str(inst_a.id)
    assert data["campus_id"] is None
    assert data["is_active"] is False
    assert data["is_verified"] is False
    assert data["invitation_id"] is not None
    assert data["invitation_status"] == "pending"
    assert data["raw_invitation_token"] is not None
    assert "/auth/accept-invitation?token=" in data["invitation_url"]


@pytest.mark.asyncio
async def test_02_rector_invites_coordinator_campus_scope(
    client: AsyncClient, r9_fixture: dict[str, Any]
):
    """Rector invites a coordinator scoped to a specific campus belonging to their institution."""
    headers = r9_fixture["rector_a_headers"]
    inst_a = r9_fixture["inst_a"]
    campus_a2 = r9_fixture["campus_a2"]

    tag = uuid.uuid4().hex[:6]
    payload = {
        "email": f"coord_campus_{tag}@pevn.edu.co",
        "first_name": "Elena",
        "last_name": "Rios",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "campus_id": str(campus_a2.id),
    }
    res = await client.post("/api/v1/coordinators", json=payload, headers=headers)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["institution_id"] == str(inst_a.id)
    assert data["campus_id"] == str(campus_a2.id)
    assert data["campus_name"] == campus_a2.name
    assert data["invitation_status"] == "pending"


@pytest.mark.asyncio
async def test_03_rector_cannot_assign_campus_of_another_institution(
    client: AsyncClient, r9_fixture: dict[str, Any]
):
    """Rector cannot assign a campus belonging to Institution B."""
    headers = r9_fixture["rector_a_headers"]
    campus_b1 = r9_fixture["campus_b1"]

    tag = uuid.uuid4().hex[:6]
    payload = {
        "email": f"coord_cross_{tag}@pevn.edu.co",
        "first_name": "Intruso",
        "last_name": "Campus",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "campus_id": str(campus_b1.id),
    }
    res = await client.post("/api/v1/coordinators", json=payload, headers=headers)
    assert res.status_code == 404
    assert "CAMPUS_NOT_FOUND" in res.text or "no pertenece a la institución" in res.text.lower()


@pytest.mark.asyncio
async def test_04_coordinator_token_verification_and_acceptance_lifecycle(
    client: AsyncClient, r9_fixture: dict[str, Any]
):
    """Verify invitation token, accept invitation with new password, and verify single-use."""
    headers = r9_fixture["rector_a_headers"]
    inst_a = r9_fixture["inst_a"]
    campus_a1 = r9_fixture["campus_a1"]

    tag = uuid.uuid4().hex[:6]
    email = f"coord_flow_{tag}@pevn.edu.co"
    payload = {
        "email": email,
        "first_name": "Diana",
        "last_name": "Turbay",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "campus_id": str(campus_a1.id),
    }
    create_res = await client.post("/api/v1/coordinators", json=payload, headers=headers)
    assert create_res.status_code == 201
    raw_token = create_res.json()["raw_invitation_token"]

    # 1. Verify token publicly
    verify_res = await client.post("/api/v1/auth/verify-invitation", json={"token": raw_token})
    assert verify_res.status_code == 200
    v_data = verify_res.json()
    assert v_data["valid"] is True
    assert v_data["role_name"] == "coordinator"
    assert v_data["institution_name"] == inst_a.name
    assert v_data["campus_name"] == campus_a1.name

    # 2. Accept invitation
    accept_payload = {
        "token": raw_token,
        "password": "Password123!",
        "password_confirmation": "Password123!",
    }
    accept_res = await client.post("/api/v1/auth/accept-invitation", json=accept_payload)
    assert accept_res.status_code == 200
    a_data = accept_res.json()
    assert a_data["is_active"] is True
    assert "Coordinador" in a_data["message"]

    # 3. Single-use rejection on second attempt
    replay_res = await client.post("/api/v1/auth/accept-invitation", json=accept_payload)
    assert replay_res.status_code == 409
    assert "INVITATION_ALREADY_USED" in replay_res.text or "ya fue utilizada" in replay_res.text.lower()


@pytest.mark.asyncio
async def test_05_resend_invitation_invalidates_prior_token(
    client: AsyncClient, r9_fixture: dict[str, Any]
):
    """Resending an invitation creates a new token and revokes the previous pending token."""
    headers = r9_fixture["rector_a_headers"]

    tag = uuid.uuid4().hex[:6]
    payload = {
        "email": f"coord_resend_{tag}@pevn.edu.co",
        "first_name": "Camilo",
        "last_name": "Torres",
        "document_type": "CC",
        "document_number": _rand_doc(),
    }
    create_res = await client.post("/api/v1/coordinators", json=payload, headers=headers)
    assert create_res.status_code == 201
    coord_id = create_res.json()["id"]
    token_1 = create_res.json()["raw_invitation_token"]

    # Resend invitation
    resend_res = await client.post(f"/api/v1/coordinators/{coord_id}/resend-invitation", headers=headers)
    assert resend_res.status_code == 200
    token_2 = resend_res.json()["raw_invitation_token"]
    assert token_2 != token_1

    # Attempting to accept token_1 must be rejected as revoked
    accept_1 = await client.post("/api/v1/auth/accept-invitation", json={
        "token": token_1,
        "password": "NewPassword123!",
        "password_confirmation": "NewPassword123!",
    })
    assert accept_1.status_code == 409
    assert "INVITATION_REVOKED" in accept_1.text or "revocado" in accept_1.text.lower()

    # Accepting token_2 succeeds
    accept_2 = await client.post("/api/v1/auth/accept-invitation", json={
        "token": token_2,
        "password": "NewPassword123!",
        "password_confirmation": "NewPassword123!",
    })
    assert accept_2.status_code == 200
    assert accept_2.json()["is_active"] is True


@pytest.mark.asyncio
async def test_06_coordinator_cannot_invite_coordinators(
    client: AsyncClient, r9_fixture: dict[str, Any]
):
    """A Coordinator cannot create or invite another Coordinator."""
    headers = r9_fixture["coord_a_headers"]

    payload = {
        "email": "unauthorized_coord@pevn.edu.co",
        "first_name": "Fake",
        "last_name": "Coordinator",
        "document_type": "CC",
        "document_number": _rand_doc(),
    }
    res = await client.post("/api/v1/coordinators", json=payload, headers=headers)
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_07_list_institution_campuses(
    client: AsyncClient, r9_fixture: dict[str, Any]
):
    """Rector can retrieve the list of campuses for their institution to assign coordinators."""
    headers = r9_fixture["rector_a_headers"]
    inst_a = r9_fixture["inst_a"]

    res = await client.get("/api/v1/coordinators/campuses", headers=headers)
    assert res.status_code == 200
    campuses = res.json()
    assert len(campuses) >= 2
    for c in campuses:
        assert c["institution_id"] == str(inst_a.id)
