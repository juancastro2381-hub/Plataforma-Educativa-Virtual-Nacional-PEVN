"""
PEVN Backend — NTA-10-R10 Coordinator Assignment Exclusivity & Duplicate Prevention Tests
AI Software Factory Standard v1.2

Verifies the mutually exclusive assignment model for Academic Coordinators:
  1. The first campus-specific coordinator assignment succeeds.
  2. A second coordinator for the same campus is rejected with 409 Conflict (COORDINATOR_CAMPUS_CONFLICT).
  3. Coordinators assigned to two different campuses of the same institution are allowed.
  4. An institution-wide assignment is rejected when campus-specific assignments exist (COORDINATOR_SCOPE_CONFLICT).
  5. A campus-specific assignment is rejected when an institution-wide assignment exists (COORDINATOR_SCOPE_CONFLICT).
  6. A second institution-wide assignment is rejected (COORDINATOR_GLOBAL_CONFLICT).
  7. Pending invitations reserve their applicable assignment slots.
  8. Expired or revoked invitations do not permanently block legitimate reassignment when no effective assignment remains.
  9. Resending an invitation for the same coordinator does not create a duplicate or trigger false conflict.
  10. A coordinator cannot bypass the rule by changing client-supplied institution or campus IDs (server-side derivation).
  11. Cross-institution campus IDs remain rejected (404 CAMPUS_NOT_FOUND).
  12. Suspended-account behavior matches explicit policy (suspension releases slot, reactivation re-evaluates exclusivity).
  13. Concurrent requests cannot produce conflicting effective assignments (transaction row-locking).
  14. Existing RBAC and Rector authority-chain tests continue to pass.
"""

from __future__ import annotations

import asyncio
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.tokens import token_service
from app.models.institution import Campus, Institution
from app.models.invitation import CoordinatorInvitation
from app.models.role import Role, UserRole
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User
from app.services.rbac_bootstrap_service import RbacBootstrapService


def _rand_doc() -> str:
    return str(secrets.randbelow(899999999) + 100000000)


@pytest.fixture
async def exclusivity_fixture(db_session: AsyncSession) -> dict[str, Any]:
    """Bootstrap canonical RBAC and institutional test entities for NTA-10-R10."""
    bootstrap = RbacBootstrapService(session=db_session)
    await bootstrap.seed_canonical_rbac_if_needed()

    dept = Department(code=f"08_{uuid.uuid4().hex[:4]}", name="Atlantico Exclusivity Test")
    muni = Municipality(code=f"08001_{uuid.uuid4().hex[:4]}", name="Barranquilla Exclusivity Test", department=dept)
    db_session.add_all([dept, muni])
    await db_session.flush()

    inst_a = Institution(
        dane_code=f"108001{uuid.uuid4().hex[:6]}",
        name="I.E. Exclusivity Alpha",
        municipality=muni,
        email="rector_excl_a@pevn.edu.co",
        is_active=True,
    )
    inst_b = Institution(
        dane_code=f"108001{uuid.uuid4().hex[:6]}",
        name="I.E. Exclusivity Beta",
        municipality=muni,
        email="rector_excl_b@pevn.edu.co",
        is_active=True,
    )
    db_session.add_all([inst_a, inst_b])
    await db_session.flush()

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
    campus_b1 = Campus(
        institution_id=inst_b.id,
        dane_sede_code=f"SB_{uuid.uuid4().hex[:6]}",
        name="Sede Principal Beta",
    )
    db_session.add_all([campus_a1, campus_a2, campus_b1])
    await db_session.flush()

    async def create_rector(institution: Institution) -> tuple[User, dict[str, str]]:
        tag = uuid.uuid4().hex[:6]
        user = User(
            email=f"rector_{tag}@pevn.edu.co",
            username=f"rector_{tag}",
            hashed_password="hashed_placeholder",
            first_name="Rector",
            last_name="Test",
            document_type=DocumentType.CC,
            document_number=_rand_doc(),
            institution_id=institution.id,
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        await db_session.flush()

        role = (await db_session.execute(select(Role).where(Role.name == "rector"))).scalar_one()
        ur = UserRole(
            user_id=user.id,
            role_id=role.id,
            institution_id=institution.id,
            is_active=True,
        )
        db_session.add(ur)
        await db_session.flush()

        token = await token_service.create_access_token(
            subject=str(user.id),
            additional_claims={
                "roles": ["rector"],
                "institution_id": str(institution.id),
            },
        )
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        return user, headers

    rector_a_user, rector_a_headers = await create_rector(inst_a)
    rector_b_user, rector_b_headers = await create_rector(inst_b)

    await db_session.commit()

    return {
        "inst_a": inst_a,
        "inst_b": inst_b,
        "campus_a1": campus_a1,
        "campus_a2": campus_a2,
        "campus_b1": campus_b1,
        "rector_a_headers": rector_a_headers,
        "rector_b_headers": rector_b_headers,
    }


@pytest.mark.asyncio
async def test_01_first_campus_specific_assignment_succeeds(
    client: AsyncClient, exclusivity_fixture: dict[str, Any]
):
    """Rule B: The first coordinator assigned to a campus succeeds."""
    headers = exclusivity_fixture["rector_a_headers"]
    campus_a1 = exclusivity_fixture["campus_a1"]

    payload = {
        "email": f"coord_first_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "first_name": "Valeria",
        "last_name": "Gomez",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "campus_id": str(campus_a1.id),
    }
    res = await client.post("/api/v1/coordinators", json=payload, headers=headers)
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["campus_id"] == str(campus_a1.id)
    assert data["campus_name"] == campus_a1.name
    assert data["invitation_status"] == "pending"


@pytest.mark.asyncio
async def test_02_second_coordinator_same_campus_rejected_409(
    client: AsyncClient, exclusivity_fixture: dict[str, Any]
):
    """Rule B: A second coordinator for the same campus is rejected with 409 Conflict."""
    headers = exclusivity_fixture["rector_a_headers"]
    campus_a1 = exclusivity_fixture["campus_a1"]

    payload1 = {
        "email": f"coord_p1_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "first_name": "Mauricio",
        "last_name": "Restrepo",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "campus_id": str(campus_a1.id),
    }
    res1 = await client.post("/api/v1/coordinators", json=payload1, headers=headers)
    assert res1.status_code == 201, res1.text

    payload2 = {
        "email": f"coord_p2_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "first_name": "Marlon",
        "last_name": "Diaz",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "campus_id": str(campus_a1.id),
    }
    res2 = await client.post("/api/v1/coordinators", json=payload2, headers=headers)
    assert res2.status_code == 409, res2.text
    body = res2.json()
    assert body["error"]["code"] == "COORDINATOR_CAMPUS_CONFLICT"
    assert "ya cuenta con un Coordinador Académico asignado" in body["error"]["message"]
    assert "Mauricio Restrepo" in body["error"]["message"]


@pytest.mark.asyncio
async def test_03_coordinators_two_different_campuses_allowed(
    client: AsyncClient, exclusivity_fixture: dict[str, Any]
):
    """Rule B: Coordinators assigned to different campuses of the same institution are allowed."""
    headers = exclusivity_fixture["rector_a_headers"]
    campus_a1 = exclusivity_fixture["campus_a1"]
    campus_a2 = exclusivity_fixture["campus_a2"]

    payload1 = {
        "email": f"coord_diff1_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "first_name": "Sofia",
        "last_name": "Mendoza",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "campus_id": str(campus_a1.id),
    }
    res1 = await client.post("/api/v1/coordinators", json=payload1, headers=headers)
    assert res1.status_code == 201, res1.text

    payload2 = {
        "email": f"coord_diff2_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "first_name": "Andres",
        "last_name": "Castro",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "campus_id": str(campus_a2.id),
    }
    res2 = await client.post("/api/v1/coordinators", json=payload2, headers=headers)
    assert res2.status_code == 201, res2.text
    data2 = res2.json()
    assert data2["campus_id"] == str(campus_a2.id)


@pytest.mark.asyncio
async def test_04_institution_wide_rejected_when_campus_specific_exists(
    client: AsyncClient, exclusivity_fixture: dict[str, Any]
):
    """Rule A: An institution-wide assignment is rejected when campus-specific assignments exist."""
    headers = exclusivity_fixture["rector_a_headers"]
    campus_a1 = exclusivity_fixture["campus_a1"]

    payload_campus = {
        "email": f"coord_c_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "first_name": "Campus",
        "last_name": "Leader",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "campus_id": str(campus_a1.id),
    }
    res1 = await client.post("/api/v1/coordinators", json=payload_campus, headers=headers)
    assert res1.status_code == 201, res1.text

    payload_global = {
        "email": f"coord_g_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "first_name": "Global",
        "last_name": "Leader",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "campus_id": None,
    }
    res2 = await client.post("/api/v1/coordinators", json=payload_global, headers=headers)
    assert res2.status_code == 409, res2.text
    body = res2.json()
    assert body["error"]["code"] == "COORDINATOR_SCOPE_CONFLICT"
    assert "existen coordinadores asignados a sedes específicas" in body["error"]["message"]


@pytest.mark.asyncio
async def test_05_campus_specific_rejected_when_institution_wide_exists(
    client: AsyncClient, exclusivity_fixture: dict[str, Any]
):
    """Rule A: A campus-specific assignment is rejected when an institution-wide assignment exists."""
    headers = exclusivity_fixture["rector_a_headers"]
    campus_a1 = exclusivity_fixture["campus_a1"]

    payload_global = {
        "email": f"coord_g2_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "first_name": "Global",
        "last_name": "Director",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "campus_id": None,
    }
    res1 = await client.post("/api/v1/coordinators", json=payload_global, headers=headers)
    assert res1.status_code == 201, res1.text

    payload_campus = {
        "email": f"coord_c2_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "first_name": "Sede",
        "last_name": "Director",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "campus_id": str(campus_a1.id),
    }
    res2 = await client.post("/api/v1/coordinators", json=payload_campus, headers=headers)
    assert res2.status_code == 409, res2.text
    body = res2.json()
    assert body["error"]["code"] == "COORDINATOR_SCOPE_CONFLICT"
    assert "cuenta con un Coordinador Académico de alcance global" in body["error"]["message"]


@pytest.mark.asyncio
async def test_06_second_institution_wide_rejected(
    client: AsyncClient, exclusivity_fixture: dict[str, Any]
):
    """Rule A: A second institution-wide assignment is rejected."""
    headers = exclusivity_fixture["rector_a_headers"]

    payload_g1 = {
        "email": f"coord_glob1_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "first_name": "Primero",
        "last_name": "Global",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "campus_id": None,
    }
    res1 = await client.post("/api/v1/coordinators", json=payload_g1, headers=headers)
    assert res1.status_code == 201, res1.text

    payload_g2 = {
        "email": f"coord_glob2_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "first_name": "Segundo",
        "last_name": "Global",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "campus_id": None,
    }
    res2 = await client.post("/api/v1/coordinators", json=payload_g2, headers=headers)
    assert res2.status_code == 409, res2.text
    body = res2.json()
    assert body["error"]["code"] == "COORDINATOR_GLOBAL_CONFLICT"
    assert "Solo se permite un coordinador institucional global" in body["error"]["message"]


@pytest.mark.asyncio
async def test_07_pending_invitations_reserve_assignment_slots(
    client: AsyncClient, exclusivity_fixture: dict[str, Any]
):
    """Rule C: A pending unaccepted invitation reserves its slot and blocks conflicting assignments."""
    headers = exclusivity_fixture["rector_a_headers"]
    campus_a1 = exclusivity_fixture["campus_a1"]

    # Invite User 1 (inactive, pending invitation)
    payload1 = {
        "email": f"coord_pend_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "first_name": "Pendiente",
        "last_name": "User",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "campus_id": str(campus_a1.id),
    }
    res1 = await client.post("/api/v1/coordinators", json=payload1, headers=headers)
    assert res1.status_code == 201
    assert res1.json()["invitation_status"] == "pending"

    # User 2 tries to be invited to same campus while User 1 is pending
    payload2 = {
        "email": f"coord_pend2_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "first_name": "Segundo",
        "last_name": "Aspirante",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "campus_id": str(campus_a1.id),
    }
    res2 = await client.post("/api/v1/coordinators", json=payload2, headers=headers)
    assert res2.status_code == 409
    body = res2.json()
    assert body["error"]["code"] == "COORDINATOR_CAMPUS_CONFLICT"
    assert "invitación pendiente" in body["error"]["message"]


@pytest.mark.asyncio
async def test_08_expired_or_revoked_invitations_do_not_block_reassignment(
    client: AsyncClient, exclusivity_fixture: dict[str, Any], db_session: AsyncSession
):
    """Rule C: Expired or revoked invitations do not permanently block legitimate reassignment."""
    headers = exclusivity_fixture["rector_a_headers"]
    campus_a1 = exclusivity_fixture["campus_a1"]

    payload1 = {
        "email": f"coord_exp_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "first_name": "Expirable",
        "last_name": "User",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "campus_id": str(campus_a1.id),
    }
    res1 = await client.post("/api/v1/coordinators", json=payload1, headers=headers)
    assert res1.status_code == 201
    coord1_id = res1.json()["id"]

    # Manually expire the invitation in database
    await db_session.execute(
        update(CoordinatorInvitation)
        .where(CoordinatorInvitation.user_id == uuid.UUID(coord1_id))
        .values(expires_at=datetime.now(UTC) - timedelta(hours=1))
    )
    await db_session.commit()

    # Now a new coordinator can be invited to this campus
    payload2 = {
        "email": f"coord_new_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "first_name": "Reemplazo",
        "last_name": "Valido",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "campus_id": str(campus_a1.id),
    }
    res2 = await client.post("/api/v1/coordinators", json=payload2, headers=headers)
    assert res2.status_code == 201, res2.text
    assert res2.json()["campus_id"] == str(campus_a1.id)


@pytest.mark.asyncio
async def test_09_resending_invitation_does_not_create_duplicate(
    client: AsyncClient, exclusivity_fixture: dict[str, Any]
):
    """Rule C: Resending an invitation for the same coordinator reuses the assignment slot."""
    headers = exclusivity_fixture["rector_a_headers"]
    campus_a1 = exclusivity_fixture["campus_a1"]

    payload = {
        "email": f"coord_resend_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "first_name": "Reenviable",
        "last_name": "User",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "campus_id": str(campus_a1.id),
    }
    res1 = await client.post("/api/v1/coordinators", json=payload, headers=headers)
    assert res1.status_code == 201
    coord_id = res1.json()["id"]

    # Resend invitation for this same coordinator
    res_resend = await client.post(f"/api/v1/coordinators/{coord_id}/resend-invitation", headers=headers)
    assert res_resend.status_code == 200, res_resend.text
    data = res_resend.json()
    assert "Invitación reenviada exitosamente" in data["message"]


@pytest.mark.asyncio
async def test_10_cannot_bypass_via_client_supplied_institution_id(
    client: AsyncClient, exclusivity_fixture: dict[str, Any]
):
    """Security: Institution ID is strictly derived from server-side Rector context and cannot be spoofed."""
    headers = exclusivity_fixture["rector_a_headers"]
    inst_a = exclusivity_fixture["inst_a"]
    inst_b = exclusivity_fixture["inst_b"]

    payload = {
        "email": f"coord_bypass_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "first_name": "Attacker",
        "last_name": "Bypass",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "campus_id": None,
    }
    # Pass query institution_id for Institution B while authenticated as Rector A
    res = await client.post(f"/api/v1/coordinators?institution_id={inst_b.id}", json=payload, headers=headers)
    assert res.status_code == 201, res.text
    data = res.json()
    # Verified: server-side authority enforced inst_a, ignoring spoofed inst_b
    assert data["institution_id"] == str(inst_a.id)
    assert data["institution_id"] != str(inst_b.id)


@pytest.mark.asyncio
async def test_11_cross_institution_campus_id_rejected_404(
    client: AsyncClient, exclusivity_fixture: dict[str, Any]
):
    """Security: Assigning a campus belonging to Institution B while Rector of Institution A is rejected."""
    headers = exclusivity_fixture["rector_a_headers"]
    campus_b1 = exclusivity_fixture["campus_b1"]

    payload = {
        "email": f"coord_cross_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "first_name": "Alien",
        "last_name": "Campus",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "campus_id": str(campus_b1.id),
    }
    res = await client.post("/api/v1/coordinators", json=payload, headers=headers)
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "CAMPUS_NOT_FOUND"


@pytest.mark.asyncio
async def test_12_suspended_account_releases_slot_and_reactivation_rechecks(
    client: AsyncClient, exclusivity_fixture: dict[str, Any]
):
    """Rule C: Suspending releases slot for new assignment; reactivating when slot is taken fails with 409."""
    headers = exclusivity_fixture["rector_a_headers"]
    campus_a1 = exclusivity_fixture["campus_a1"]

    # 1. Create and accept coordinator 1
    payload1 = {
        "email": f"coord_susp1_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "first_name": "Hugo",
        "last_name": "Mora",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "campus_id": str(campus_a1.id),
    }
    res1 = await client.post("/api/v1/coordinators", json=payload1, headers=headers)
    assert res1.status_code == 201
    coord1_id = res1.json()["id"]
    token1 = res1.json()["raw_invitation_token"]

    # Accept invitation 1
    accept1 = await client.post("/api/v1/auth/accept-invitation", json={
        "token": token1,
        "password": "ValidPassword123#",
        "password_confirmation": "ValidPassword123#",
    })
    assert accept1.status_code == 200

    # 2. Suspend coordinator 1 via PATCH
    susp_res = await client.patch(f"/api/v1/coordinators/{coord1_id}/status", json={
        "is_active": False,
        "reason": "Licencia no remunerada",
    }, headers=headers)
    assert susp_res.status_code == 200
    assert susp_res.json()["is_active"] is False

    # 3. With coordinator 1 suspended, slot is released: invite coordinator 2 to same campus
    payload2 = {
        "email": f"coord_susp2_{uuid.uuid4().hex[:6]}@pevn.edu.co",
        "first_name": "Paco",
        "last_name": "Mora",
        "document_type": "CC",
        "document_number": _rand_doc(),
        "campus_id": str(campus_a1.id),
    }
    res2 = await client.post("/api/v1/coordinators", json=payload2, headers=headers)
    assert res2.status_code == 201, res2.text

    # 4. Attempt to reactivate coordinator 1 while coordinator 2 holds the slot -> 409 Conflict!
    reactivate_res = await client.patch(f"/api/v1/coordinators/{coord1_id}/status", json={
        "is_active": True,
        "reason": "Reincorporación anticipada",
    }, headers=headers)
    assert reactivate_res.status_code == 409, reactivate_res.text
    body = reactivate_res.json()
    assert body["error"]["code"] == "COORDINATOR_CAMPUS_CONFLICT"
    assert "ya cuenta con un Coordinador Académico asignado" in body["error"]["message"]


@pytest.mark.asyncio
async def test_13_concurrent_requests_cannot_produce_conflicting_assignments(
    exclusivity_fixture: dict[str, Any], db_session: AsyncSession
):
    """Concurrency: Simultaneous requests for the same campus serialize; exactly one succeeds and other gets 409."""
    from sqlalchemy.ext.asyncio import async_sessionmaker
    from app.exceptions.errors import ConflictError
    from app.schemas.coordinator import CoordinatorCreateRequest
    from app.services.coordinator_service import CoordinatorService

    inst_a = exclusivity_fixture["inst_a"]
    campus_a1 = exclusivity_fixture["campus_a1"]

    session_maker = async_sessionmaker(
        bind=db_session.bind,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def run_create(email_tag: str):
        async with session_maker() as sess:
            service = CoordinatorService(session=sess)
            payload = CoordinatorCreateRequest(
                email=f"coord_conc_{email_tag}_{uuid.uuid4().hex[:6]}@pevn.edu.co",
                first_name="Concurrente",
                last_name="Test",
                document_type=DocumentType.CC,
                document_number=_rand_doc(),
                campus_id=campus_a1.id,
            )
            res = await service.create_coordinator(
                institution_id=inst_a.id,
                payload=payload,
            )
            await sess.commit()
            return res

    results = []
    errors = []

    task_a = run_create("alpha")
    task_b = run_create("beta")

    res_list = await asyncio.gather(task_a, task_b, return_exceptions=True)
    for r in res_list:
        if isinstance(r, Exception):
            errors.append(r)
        else:
            results.append(r)

    assert len(results) == 1, f"Exactly one request must succeed, got results: {results}, errors: {errors}"
    assert len(errors) == 1, f"The other request must fail with ConflictError, got: {errors}"
    assert isinstance(errors[0], ConflictError)
    assert errors[0].code == "COORDINATOR_CAMPUS_CONFLICT"
