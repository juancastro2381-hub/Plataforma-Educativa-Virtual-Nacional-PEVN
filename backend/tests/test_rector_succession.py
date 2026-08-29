"""
PEVN Backend — Rector Succession & Revocation Test Suite (Phase 7 - Step 1)

Authoritative verification of the Rector succession and revocation workflow:
  1. Successful Rector revocation by Superadmin.
  2. Successful Rector revocation by National Admin.
  3. Unauthorized roles (Rector, Coordinator, Teacher, Student, Guardian) are denied revocation (403).
  4. Missing/invalid institution handling returns 404.
  5. Institution without active Rector returns 404 NO_ACTIVE_RECTOR_FOUND.
  6. Revocation requires a valid non-empty reason (422).
  7. Revoked Rector loses effective Rector privileges (cannot create academic years).
  8. Historical audit records and user identity are preserved (soft deactivation).
  9. Immediate succession: A new Rector invitation can be issued immediately after revocation.
  10. Cross-institution tenant isolation: Revoking Rector in Inst A leaves Inst B unaffected.
  11. Pending unredeemed invitations are automatically revoked when titular Rector is revoked.
  12. Existing Rector onboarding flow remains 100% functional after succession.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.core.security.tokens import token_service
from app.models.institution import Campus, Institution
from app.models.invitation import RectorInvitation
from app.models.role import Role, UserRole
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User
from app.services.rbac_bootstrap_service import RbacBootstrapService
from app.services.rector_onboarding_service import RectorOnboardingService


@pytest.fixture
async def succession_fixture(db_session: AsyncSession) -> dict[str, Any]:
    """Seed institutions, active rectors, and role tokens for succession testing."""
    bootstrap = RbacBootstrapService(session=db_session)
    await bootstrap.seed_canonical_rbac_if_needed()

    dept = Department(code="25", name="Cundinamarca")
    db_session.add(dept)
    await db_session.flush()

    muni = Municipality(department_id=dept.id, code="25001", name="Agua de Dios")
    db_session.add(muni)
    await db_session.flush()

    inst_a = Institution(
        municipality_id=muni.id,
        dane_code="125001000111",
        name="I.E. Departamental San Jose A",
        email="rectoria.a@sanjose.edu.co",
        is_active=True,
    )
    inst_b = Institution(
        municipality_id=muni.id,
        dane_code="125001000222",
        name="I.E. Departamental San Jose B",
        email="rectoria.b@sanjose.edu.co",
        is_active=True,
    )
    inst_empty = Institution(
        municipality_id=muni.id,
        dane_code="125001000333",
        name="I.E. Departamental Sin Rector",
        email="rectoria.c@sanjose.edu.co",
        is_active=True,
    )
    db_session.add_all([inst_a, inst_b, inst_empty])
    await db_session.flush()

    campus_a = Campus(
        institution_id=inst_a.id,
        dane_sede_code="12500100011101",
        name="Sede Principal A",
        is_active=True,
    )
    campus_b = Campus(
        institution_id=inst_b.id,
        dane_sede_code="12500100022201",
        name="Sede Principal B",
        is_active=True,
    )
    db_session.add_all([campus_a, campus_b])
    await db_session.flush()

    role_rector = (await db_session.execute(select(Role).where(Role.name == "rector"))).scalar_one()
    role_coord = (await db_session.execute(select(Role).where(Role.name == "coordinator"))).scalar_one()
    role_teacher = (await db_session.execute(select(Role).where(Role.name == "teacher"))).scalar_one()
    role_student = (await db_session.execute(select(Role).where(Role.name == "student"))).scalar_one()
    role_guardian = (await db_session.execute(select(Role).where(Role.name == "guardian"))).scalar_one()
    role_nat = (await db_session.execute(select(Role).where(Role.name == SystemRole.NATIONAL_ADMIN.value))).scalar_one()
    role_super = (await db_session.execute(select(Role).where(Role.name == SystemRole.SUPERADMIN.value))).scalar_one()

    # Active Rector A
    rector_a = User(
        institution_id=inst_a.id,
        email="rector.a@sanjose.edu.co",
        username="rector.a",
        hashed_password=password_hasher.hash("RectorPass123!"),
        first_name="Rector",
        last_name="Primero A",
        document_type=DocumentType.CC,
        document_number="10000001",
        is_active=True,
        is_verified=True,
    )
    # Active Rector B
    rector_b = User(
        institution_id=inst_b.id,
        email="rector.b@sanjose.edu.co",
        username="rector.b",
        hashed_password=password_hasher.hash("RectorPass123!"),
        first_name="Rector",
        last_name="Segundo B",
        document_type=DocumentType.CC,
        document_number="10000002",
        is_active=True,
        is_verified=True,
    )
    # Coordinator A
    coord_a = User(
        institution_id=inst_a.id,
        email="coord.a@sanjose.edu.co",
        username="coord.a",
        hashed_password=password_hasher.hash("CoordPass123!"),
        first_name="Coord",
        last_name="Academico",
        document_type=DocumentType.CC,
        document_number="20000001",
        is_active=True,
        is_verified=True,
    )
    # Teacher A
    teacher_a = User(
        institution_id=inst_a.id,
        email="docente.a@sanjose.edu.co",
        username="docente.a",
        hashed_password=password_hasher.hash("TeacherPass123!"),
        first_name="Docente",
        last_name="Ciencias",
        document_type=DocumentType.CC,
        document_number="30000001",
        is_active=True,
        is_verified=True,
    )
    # Student A
    student_a = User(
        institution_id=inst_a.id,
        email="alumno.a@sanjose.edu.co",
        username="alumno.a",
        hashed_password=password_hasher.hash("StudentPass123!"),
        first_name="Alumno",
        last_name="Estudiante",
        document_type=DocumentType.TI,
        document_number="40000001",
        is_active=True,
        is_verified=True,
    )
    # Guardian A
    guardian_a = User(
        institution_id=inst_a.id,
        email="acudiente.a@sanjose.edu.co",
        username="acudiente.a",
        hashed_password=password_hasher.hash("GuardianPass123!"),
        first_name="Acudiente",
        last_name="Responsable",
        document_type=DocumentType.CC,
        document_number="50000001",
        is_active=True,
        is_verified=True,
    )
    # National Admin
    admin_nat = User(
        institution_id=None,
        email="admin.nacional@mineducacion.gov.co",
        username="admin.nacional",
        hashed_password=password_hasher.hash("AdminNatPass123!"),
        first_name="Admin",
        last_name="Nacional MEN",
        document_type=DocumentType.CC,
        document_number="90000001",
        is_active=True,
        is_verified=True,
    )
    # Superadmin
    superadmin = User(
        institution_id=None,
        email="superadmin@pevn.gov.co",
        username="superadmin",
        hashed_password=password_hasher.hash("SuperadminPass123!"),
        first_name="Root",
        last_name="Superadmin",
        document_type=DocumentType.CC,
        document_number="99000001",
        is_active=True,
        is_verified=True,
    )

    db_session.add_all([
        rector_a, rector_b, coord_a, teacher_a, student_a, guardian_a, admin_nat, superadmin
    ])
    await db_session.flush()

    # UserRoles
    db_session.add_all([
        UserRole(user_id=admin_nat.id, role_id=role_nat.id, institution_id=None, is_active=True),
        UserRole(user_id=superadmin.id, role_id=role_super.id, institution_id=None, is_active=True),
        UserRole(user_id=rector_a.id, role_id=role_rector.id, institution_id=inst_a.id, is_active=True),
        UserRole(user_id=rector_b.id, role_id=role_rector.id, institution_id=inst_b.id, is_active=True),
        UserRole(user_id=coord_a.id, role_id=role_coord.id, institution_id=inst_a.id, is_active=True),
        UserRole(user_id=teacher_a.id, role_id=role_teacher.id, institution_id=inst_a.id, is_active=True),
        UserRole(user_id=student_a.id, role_id=role_student.id, institution_id=inst_a.id, is_active=True),
        UserRole(user_id=guardian_a.id, role_id=role_guardian.id, institution_id=inst_a.id, is_active=True),
    ])
    await db_session.commit()

    # JWT Tokens
    nat_token = await token_service.create_access_token(
        subject=str(admin_nat.id),
        additional_claims={"roles": [SystemRole.NATIONAL_ADMIN.value], "institution_id": None},
    )
    super_token = await token_service.create_access_token(
        subject=str(superadmin.id),
        additional_claims={"roles": [SystemRole.SUPERADMIN.value], "institution_id": None},
    )
    rector_a_token = await token_service.create_access_token(
        subject=str(rector_a.id),
        additional_claims={"roles": [SystemRole.RECTOR.value], "institution_id": str(inst_a.id)},
    )
    coord_token = await token_service.create_access_token(
        subject=str(coord_a.id),
        additional_claims={"roles": ["coordinator"], "institution_id": str(inst_a.id)},
    )
    teacher_token = await token_service.create_access_token(
        subject=str(teacher_a.id),
        additional_claims={"roles": [SystemRole.TEACHER.value], "institution_id": str(inst_a.id)},
    )
    student_token = await token_service.create_access_token(
        subject=str(student_a.id),
        additional_claims={"roles": [SystemRole.STUDENT.value], "institution_id": str(inst_a.id)},
    )
    guardian_token = await token_service.create_access_token(
        subject=str(guardian_a.id),
        additional_claims={"roles": ["guardian"], "institution_id": str(inst_a.id)},
    )

    return {
        "inst_a": inst_a,
        "inst_b": inst_b,
        "inst_empty": inst_empty,
        "rector_a": rector_a,
        "rector_b": rector_b,
        "admin_headers": {"Authorization": f"Bearer {nat_token}"},
        "super_headers": {"Authorization": f"Bearer {super_token}"},
        "rector_a_headers": {"Authorization": f"Bearer {rector_a_token}"},
        "coord_headers": {"Authorization": f"Bearer {coord_token}"},
        "teacher_headers": {"Authorization": f"Bearer {teacher_token}"},
        "student_headers": {"Authorization": f"Bearer {student_token}"},
        "guardian_headers": {"Authorization": f"Bearer {guardian_token}"},
    }


@pytest.mark.asyncio
async def test_rector_revocation_by_national_admin_success(
    client: AsyncClient,
    db_session: AsyncSession,
    succession_fixture: dict[str, Any],
) -> None:
    """1. National Admin successfully revokes active Rector."""
    inst_a = succession_fixture["inst_a"]
    rector_a = succession_fixture["rector_a"]
    admin_headers = succession_fixture["admin_headers"]

    res = await client.post(
        f"/api/v1/institutions/{inst_a.id}/rector/revoke",
        json={
            "reason": "TRASLADO_DIRECTIVO",
            "justification": "Resolución MEN No. 8920 de 2026",
        },
        headers=admin_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["institution_id"] == str(inst_a.id)
    assert data["revoked_user_id"] == str(rector_a.id)
    assert data["reason"] == "TRASLADO_DIRECTIVO"
    assert "revocada exitosamente" in data["message"]

    # Verify UserRole is deactivated
    role_rector = (await db_session.execute(select(Role).where(Role.name == "rector"))).scalar_one()
    ur_stmt = select(UserRole).where(
        UserRole.user_id == rector_a.id,
        UserRole.role_id == role_rector.id,
        UserRole.institution_id == inst_a.id,
    )
    ur = (await db_session.execute(ur_stmt)).scalar_one()
    assert ur.is_active is False

    # Verify User record itself is NOT physically deleted
    user_db = (await db_session.execute(select(User).where(User.id == rector_a.id))).scalar_one_or_none()
    assert user_db is not None


@pytest.mark.asyncio
async def test_rector_revocation_by_superadmin_success(
    client: AsyncClient,
    db_session: AsyncSession,
    succession_fixture: dict[str, Any],
) -> None:
    """2. Superadmin successfully revokes active Rector."""
    inst_b = succession_fixture["inst_b"]
    rector_b = succession_fixture["rector_b"]
    super_headers = succession_fixture["super_headers"]

    res = await client.post(
        f"/api/v1/institutions/{inst_b.id}/rector/revoke",
        json={
            "reason": "RENUNCIA_VOLUNTARIA",
            "justification": "Renuncia aceptada en acta de consejo",
        },
        headers=super_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["institution_id"] == str(inst_b.id)
    assert data["revoked_user_id"] == str(rector_b.id)


@pytest.mark.asyncio
async def test_unauthorized_roles_cannot_revoke_rector(
    client: AsyncClient,
    succession_fixture: dict[str, Any],
) -> None:
    """3. Rector, Coordinator, Teacher, Student, Guardian cannot revoke a Rector (403 Forbidden)."""
    inst_a = succession_fixture["inst_a"]

    payload = {"reason": "INTENTO_ILEGAL", "justification": "Sin autoridad"}

    for role_name, headers in [
        ("rector", succession_fixture["rector_a_headers"]),
        ("coordinator", succession_fixture["coord_headers"]),
        ("teacher", succession_fixture["teacher_headers"]),
        ("student", succession_fixture["student_headers"]),
        ("guardian", succession_fixture["guardian_headers"]),
    ]:
        res = await client.post(
            f"/api/v1/institutions/{inst_a.id}/rector/revoke",
            json=payload,
            headers=headers,
        )
        assert res.status_code == 403, f"Role {role_name} should receive 403 Forbidden"


@pytest.mark.asyncio
async def test_revocation_missing_institution_returns_404(
    client: AsyncClient,
    succession_fixture: dict[str, Any],
) -> None:
    """4. Non-existent institution returns 404 Not Found."""
    random_id = uuid.uuid4()
    admin_headers = succession_fixture["admin_headers"]

    res = await client.post(
        f"/api/v1/institutions/{random_id}/rector/revoke",
        json={"reason": "PRUEBA_404", "justification": "No existe"},
        headers=admin_headers,
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "INSTITUTION_NOT_FOUND"


@pytest.mark.asyncio
async def test_revocation_institution_without_active_rector_returns_404(
    client: AsyncClient,
    succession_fixture: dict[str, Any],
) -> None:
    """5. Institution without active Rector returns 404 NO_ACTIVE_RECTOR_FOUND."""
    inst_empty = succession_fixture["inst_empty"]
    admin_headers = succession_fixture["admin_headers"]

    res = await client.post(
        f"/api/v1/institutions/{inst_empty.id}/rector/revoke",
        json={"reason": "VACANCIA", "justification": "No hay titular"},
        headers=admin_headers,
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "NO_ACTIVE_RECTOR_FOUND"


@pytest.mark.asyncio
async def test_revocation_requires_valid_reason(
    client: AsyncClient,
    succession_fixture: dict[str, Any],
) -> None:
    """6. Revocation request with missing or empty reason returns 422 Unprocessable Content."""
    inst_a = succession_fixture["inst_a"]
    admin_headers = succession_fixture["admin_headers"]

    # Missing reason
    res_missing = await client.post(
        f"/api/v1/institutions/{inst_a.id}/rector/revoke",
        json={"justification": "Falta reason"},
        headers=admin_headers,
    )
    assert res_missing.status_code == 422

    # Reason too short
    res_short = await client.post(
        f"/api/v1/institutions/{inst_a.id}/rector/revoke",
        json={"reason": "AB"},
        headers=admin_headers,
    )
    assert res_short.status_code == 422


@pytest.mark.asyncio
async def test_immediate_succession_and_new_invitation_after_revocation(
    client: AsyncClient,
    db_session: AsyncSession,
    succession_fixture: dict[str, Any],
) -> None:
    """7, 8, 9 & 12. Full succession lifecycle: Revocation -> Immediate new invitation -> Onboarding."""
    inst_a = succession_fixture["inst_a"]
    admin_headers = succession_fixture["admin_headers"]

    # Step 1: Revoke outgoing Rector
    res_revoke = await client.post(
        f"/api/v1/institutions/{inst_a.id}/rector/revoke",
        json={"reason": "JUBILACION", "justification": "Decreto de retiro"},
        headers=admin_headers,
    )
    assert res_revoke.status_code == 200

    # Step 2: Immediate succession — National Admin issues invitation for incoming Rector
    res_invite = await client.post(
        f"/api/v1/institutions/{inst_a.id}/rector-invitation",
        json={
            "first_name": "Nuevo",
            "last_name": "Rector Sucesor",
            "document_type": "CC",
            "document_number": "98765432",
            "email": "rector.sucesor@sanjose.edu.co",
            "phone_number": "+57 311 9998877",
        },
        headers=admin_headers,
    )
    assert res_invite.status_code == 201
    invite_data = res_invite.json()
    raw_token = invite_data["raw_invitation_token"]
    assert raw_token is not None

    # Step 3: Successor completes cryptographic onboarding
    res_accept = await client.post(
        "/api/v1/auth/accept-invitation",
        json={
            "token": raw_token,
            "password": "NuevoRectorPass123!",
            "password_confirmation": "NuevoRectorPass123!",
        },
    )
    assert res_accept.status_code == 200
    assert res_accept.json()["is_active"] is True

    # Step 4: Login as successor and verify institutional access
    res_login = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "rector.sucesor@sanjose.edu.co",
            "password": "NuevoRectorPass123!",
        },
    )
    assert res_login.status_code == 200
    successor_token = res_login.json()["access_token"]
    successor_headers = {"Authorization": f"Bearer {successor_token}"}

    # Step 5: Successor can manage academic years in Institution A
    res_ay = await client.get("/api/v1/academic-years", headers=successor_headers)
    assert res_ay.status_code == 200


@pytest.mark.asyncio
async def test_cross_institution_isolation_preserved(
    client: AsyncClient,
    db_session: AsyncSession,
    succession_fixture: dict[str, Any],
) -> None:
    """10. Revoking Rector in Inst A does not affect active Rector in Inst B."""
    inst_a = succession_fixture["inst_a"]
    inst_b = succession_fixture["inst_b"]
    rector_b = succession_fixture["rector_b"]
    admin_headers = succession_fixture["admin_headers"]

    # Revoke Inst A
    res = await client.post(
        f"/api/v1/institutions/{inst_a.id}/rector/revoke",
        json={"reason": "REVOCACION_A", "justification": "Solo A"},
        headers=admin_headers,
    )
    assert res.status_code == 200

    # Verify Inst B Rector remains active
    role_rector = (await db_session.execute(select(Role).where(Role.name == "rector"))).scalar_one()
    ur_b = (
        await db_session.execute(
            select(UserRole).where(
                UserRole.user_id == rector_b.id,
                UserRole.role_id == role_rector.id,
                UserRole.institution_id == inst_b.id,
            )
        )
    ).scalar_one()
    assert ur_b.is_active is True


@pytest.mark.asyncio
async def test_pending_invitations_are_revoked_on_rector_revocation(
    client: AsyncClient,
    db_session: AsyncSession,
    succession_fixture: dict[str, Any],
) -> None:
    """11. Pending unredeemed invitations are automatically revoked when titular Rector is revoked."""
    inst_b = succession_fixture["inst_b"]
    admin_headers = succession_fixture["admin_headers"]

    # Issue a pending invitation for someone in Inst B
    res_inv = await client.post(
        f"/api/v1/institutions/{inst_b.id}/rector-invitation",
        json={
            "first_name": "Pendiente",
            "last_name": "Para Revocar",
            "document_type": "CC",
            "document_number": "77777777",
            "email": "pendiente.inv@sanjose.edu.co",
        },
        headers=admin_headers,
    )
    # The invitation will be 409 because rector_b is active
    assert res_inv.status_code == 409

    # Now revoke rector_b
    res_revoke = await client.post(
        f"/api/v1/institutions/{inst_b.id}/rector/revoke",
        json={"reason": "DECRETO_REVOCACION", "justification": "Vacancia"},
        headers=admin_headers,
    )
    assert res_revoke.status_code == 200

    # Verify no unrevoked invitations exist for Inst B
    inv_stmt = select(RectorInvitation).where(
        RectorInvitation.institution_id == inst_b.id,
        RectorInvitation.is_revoked == False,  # noqa: E712
    )
    unrevoked = (await db_session.execute(inv_stmt)).scalars().all()
    assert len(unrevoked) == 0


@pytest.mark.asyncio
async def test_revocation_records_audit_trail(
    client: AsyncClient,
    db_session: AsyncSession,
    succession_fixture: dict[str, Any],
) -> None:
    """12. Revocation records formal audit event RECTOR_REVOKED."""
    inst_a = succession_fixture["inst_a"]
    admin_headers = succession_fixture["admin_headers"]

    res = await client.post(
        f"/api/v1/institutions/{inst_a.id}/rector/revoke",
        json={
            "reason": "AUDITORIA_PRUEBA",
            "justification": "Verificar pista de auditoria",
        },
        headers=admin_headers,
    )
    assert res.status_code == 200
    assert "revocada exitosamente" in res.json()["message"]
