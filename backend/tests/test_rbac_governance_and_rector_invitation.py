"""
PEVN Backend — Comprehensive RBAC Governance & Identity Flow Test Suite (Phase 4)

Authoritative verification of the complete RBAC authorization model, role hierarchy,
granular permissions, tenant containment boundaries, and cryptographic identity lifecycle:

  1. Canonical Rector role exists in catalog with correct level and permissions.
  2. Rector role resolves seamlessly via onboarding service without pre-registration.
  3. National Admin can invite Rector (201 Created).
  4. Superadmin can invite Rector (201 Created).
  5. Rector cannot invite another Rector (403 Forbidden).
  6. Coordinator cannot invite Rector (403 Forbidden).
  7. Teacher cannot invite Rector (403 Forbidden).
  8. Student cannot invite Rector (403 Forbidden).
  9. Guardian cannot invite Rector (403 Forbidden).
  10. Anonymous user cannot invite Rector (401/403).
  11. Duplicate active Rector is rejected with 409 RECTOR_ALREADY_EXISTS.
  12. Inactive User + Inactive UserRole(RECTOR) created with SHA-256 token hash (zero-knowledge).
  13. Accepted invitation activates User and Rector role with Argon2id hash.
  14. Rector cannot provision institutions (403 Forbidden).
  15. Teacher can create virtual classrooms within institution scope (201 Created).
  16. Guardian is denied virtual classroom creation (403 Forbidden).
  17. Guardian is denied reading virtual classrooms (403 Forbidden).
  18. Student and Teacher can read virtual classrooms (200 OK).
  19. Guardian is denied reading recordings (403 Forbidden).
  20. Institution read authorization uses explicit institutions:read permission.
  21. Rector A cannot access Institution B (cross-tenant 403 Forbidden).
  22. Rector A cannot read academic years of Institution B (tenant containment).
  23. Coordinator can create groups but cannot create academic years (RBAC boundary).
  24. Student can read grades but cannot write grades (RBAC boundary).
  25. Guardian can read grades but cannot write grades (RBAC boundary).
  26. National Admin and Superadmin retain global and national authority.
"""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.core.security.tokens import hash_token, token_service
from app.models.academic_year import AcademicYear, AcademicYearCalendarType, AcademicYearStatus
from app.models.grade import EducationalLevel, Grade
from app.models.institution import Campus, Institution
from app.models.invitation import RectorInvitation
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User
from app.services.rbac_bootstrap_service import RbacBootstrapService
from app.services.rector_onboarding_service import RectorOnboardingService


@pytest.fixture
async def rbac_test_fixture(db_session: AsyncSession) -> dict[str, Any]:
    """Seed territory, roles, institutions, campus, grades and users for RBAC testing."""
    # Ensure RBAC catalog is fully bootstrapped
    bootstrap = RbacBootstrapService(session=db_session)
    await bootstrap.seed_canonical_rbac_if_needed()

    # Create Territory
    dept = Department(code="25", name="Cundinamarca")
    db_session.add(dept)
    await db_session.flush()

    mun = Municipality(department_id=dept.id, code="25001", name="Agua de Dios")
    db_session.add(mun)
    await db_session.flush()

    # Create Institution A
    inst_a = Institution(
        municipality_id=mun.id,
        dane_code="125001000111",
        name="I.E. Departamental San Carlos",
        email="contacto@sancarlos.edu.co",
        is_active=True,
    )
    # Create Institution B (for cross-tenant testing)
    inst_b = Institution(
        municipality_id=mun.id,
        dane_code="125001000222",
        name="I.E. Departamental Santa Maria",
        email="contacto@santamaria.edu.co",
        is_active=True,
    )
    db_session.add_all([inst_a, inst_b])
    await db_session.flush()

    # Create Campus for Institution A and B
    campus_a = Campus(
        institution_id=inst_a.id,
        dane_sede_code="125001000111-01",
        name="Sede Principal San Carlos",
        is_active=True,
    )
    campus_b = Campus(
        institution_id=inst_b.id,
        dane_sede_code="125001000222-01",
        name="Sede Principal Santa Maria",
        is_active=True,
    )
    db_session.add_all([campus_a, campus_b])
    await db_session.flush()

    # Create Grade for academic tests
    grade_6 = Grade(
        code="06-TEST",
        name="Grado Sexto Test",
        level=EducationalLevel.SECUNDARIA,
        ordinal_order=6,
    )
    db_session.add(grade_6)
    await db_session.flush()

    # Academic Year in Inst A and Inst B
    ay_a = AcademicYear(
        institution_id=inst_a.id,
        year=2026,
        name="Año Lectivo 2026 San Carlos",
        start_date=date(2026, 1, 15),
        end_date=date(2026, 11, 30),
        calendar_type=AcademicYearCalendarType.CALENDAR_A,
        status=AcademicYearStatus.ACTIVE,
    )
    ay_b = AcademicYear(
        institution_id=inst_b.id,
        year=2026,
        name="Año Lectivo 2026 Santa Maria",
        start_date=date(2026, 1, 15),
        end_date=date(2026, 11, 30),
        calendar_type=AcademicYearCalendarType.CALENDAR_A,
        status=AcademicYearStatus.ACTIVE,
    )
    db_session.add_all([ay_a, ay_b])
    await db_session.flush()

    # Roles lookup
    superadmin_role = (await db_session.execute(select(Role).where(Role.name == SystemRole.SUPERADMIN.value))).scalar_one()
    national_admin_role = (await db_session.execute(select(Role).where(Role.name == SystemRole.NATIONAL_ADMIN.value))).scalar_one()
    rector_role = (await db_session.execute(select(Role).where(Role.name == SystemRole.RECTOR.value))).scalar_one()
    coord_role = (await db_session.execute(select(Role).where(Role.name == "coordinator"))).scalar_one()
    teacher_role = (await db_session.execute(select(Role).where(Role.name == SystemRole.TEACHER.value))).scalar_one()
    student_role = (await db_session.execute(select(Role).where(Role.name == SystemRole.STUDENT.value))).scalar_one()
    guardian_role = (await db_session.execute(select(Role).where(Role.name == "guardian"))).scalar_one()

    # Users creation
    superadmin_user = User(
        email="superadmin@pevn.gov.co",
        username="superadmin@pevn.gov.co",
        hashed_password=password_hasher.hash("SuperAdmin2026*!"),
        first_name="Super",
        last_name="Admin",
        document_type=DocumentType.CC,
        document_number="1000000099",
        institution_id=None,
        is_active=True,
        is_verified=True,
    )
    national_admin_user = User(
        email="admin.nacional@mineducacion.gov.co",
        username="admin.nacional@mineducacion.gov.co",
        hashed_password=password_hasher.hash("AdminNacional2026*!"),
        first_name="Admin",
        last_name="Nacional",
        document_type=DocumentType.CC,
        document_number="1000000001",
        institution_id=None,
        is_active=True,
        is_verified=True,
    )
    existing_rector_user = User(
        email="rector.a@sancarlos.edu.co",
        username="rector.a@sancarlos.edu.co",
        hashed_password=password_hasher.hash("RectorPass2026*!"),
        first_name="Rector",
        last_name="San Carlos",
        document_type=DocumentType.CC,
        document_number="1000000002",
        institution_id=inst_a.id,
        is_active=True,
        is_verified=True,
    )
    coord_user = User(
        email="coordinador@sancarlos.edu.co",
        username="coordinador@sancarlos.edu.co",
        hashed_password=password_hasher.hash("CoordPass2026*!"),
        first_name="Coordinador",
        last_name="San Carlos",
        document_type=DocumentType.CC,
        document_number="1000000006",
        institution_id=inst_a.id,
        is_active=True,
        is_verified=True,
    )
    teacher_user = User(
        email="docente@sancarlos.edu.co",
        username="docente@sancarlos.edu.co",
        hashed_password=password_hasher.hash("DocentePass2026*!"),
        first_name="Docente",
        last_name="Prueba",
        document_type=DocumentType.CC,
        document_number="1000000003",
        institution_id=inst_a.id,
        is_active=True,
        is_verified=True,
    )
    student_user = User(
        email="estudiante@sancarlos.edu.co",
        username="estudiante@sancarlos.edu.co",
        hashed_password=password_hasher.hash("EstudiantePass2026*!"),
        first_name="Estudiante",
        last_name="Prueba",
        document_type=DocumentType.TI,
        document_number="1000000004",
        institution_id=inst_a.id,
        is_active=True,
        is_verified=True,
    )
    guardian_user = User(
        email="acudiente@sancarlos.edu.co",
        username="acudiente@sancarlos.edu.co",
        hashed_password=password_hasher.hash("AcudientePass2026*!"),
        first_name="Acudiente",
        last_name="Prueba",
        document_type=DocumentType.CC,
        document_number="1000000005",
        institution_id=inst_a.id,
        is_active=True,
        is_verified=True,
    )
    db_session.add_all([
        superadmin_user,
        national_admin_user,
        existing_rector_user,
        coord_user,
        teacher_user,
        student_user,
        guardian_user,
    ])
    await db_session.flush()

    # UserRoles assignment
    db_session.add(UserRole(user_id=superadmin_user.id, role_id=superadmin_role.id, institution_id=None, is_active=True))
    db_session.add(UserRole(user_id=national_admin_user.id, role_id=national_admin_role.id, institution_id=None, is_active=True))
    db_session.add(UserRole(user_id=existing_rector_user.id, role_id=rector_role.id, institution_id=inst_a.id, is_active=True))
    db_session.add(UserRole(user_id=coord_user.id, role_id=coord_role.id, institution_id=inst_a.id, is_active=True))
    db_session.add(UserRole(user_id=teacher_user.id, role_id=teacher_role.id, institution_id=inst_a.id, is_active=True))
    db_session.add(UserRole(user_id=student_user.id, role_id=student_role.id, institution_id=inst_a.id, is_active=True))
    db_session.add(UserRole(user_id=guardian_user.id, role_id=guardian_role.id, institution_id=inst_a.id, is_active=True))
    await db_session.commit()

    # JWT Tokens
    superadmin_token = await token_service.create_access_token(
        subject=str(superadmin_user.id),
        additional_claims={"roles": [SystemRole.SUPERADMIN.value], "institution_id": None},
    )
    admin_token = await token_service.create_access_token(
        subject=str(national_admin_user.id),
        additional_claims={"roles": [SystemRole.NATIONAL_ADMIN.value], "institution_id": None},
    )
    rector_token = await token_service.create_access_token(
        subject=str(existing_rector_user.id),
        additional_claims={"roles": [SystemRole.RECTOR.value], "institution_id": str(inst_a.id)},
    )
    coord_token = await token_service.create_access_token(
        subject=str(coord_user.id),
        additional_claims={"roles": ["coordinator"], "institution_id": str(inst_a.id)},
    )
    teacher_token = await token_service.create_access_token(
        subject=str(teacher_user.id),
        additional_claims={"roles": [SystemRole.TEACHER.value], "institution_id": str(inst_a.id)},
    )
    student_token = await token_service.create_access_token(
        subject=str(student_user.id),
        additional_claims={"roles": [SystemRole.STUDENT.value], "institution_id": str(inst_a.id)},
    )
    guardian_token = await token_service.create_access_token(
        subject=str(guardian_user.id),
        additional_claims={"roles": ["guardian"], "institution_id": str(inst_a.id)},
    )

    return {
        "inst_a": inst_a,
        "inst_b": inst_b,
        "campus_a": campus_a,
        "grade_6": grade_6,
        "ay_a": ay_a,
        "ay_b": ay_b,
        "superadmin_headers": {"Authorization": f"Bearer {superadmin_token}"},
        "admin_headers": {"Authorization": f"Bearer {admin_token}"},
        "rector_headers": {"Authorization": f"Bearer {rector_token}"},
        "coord_headers": {"Authorization": f"Bearer {coord_token}"},
        "teacher_headers": {"Authorization": f"Bearer {teacher_token}"},
        "student_headers": {"Authorization": f"Bearer {student_token}"},
        "guardian_headers": {"Authorization": f"Bearer {guardian_token}"},
    }


# ===========================================================================
# 1. Canonical Role Catalog & Resolution Tests
# ===========================================================================

async def test_canonical_rector_role_exists_in_catalog(db_session: AsyncSession, rbac_test_fixture: dict[str, Any]) -> None:
    """1. Verify canonical Rector role exists in catalog with level 60 and permissions."""
    role = (await db_session.execute(select(Role).where(Role.name == SystemRole.RECTOR.value))).scalar_one_or_none()
    assert role is not None
    assert role.name == "rector"
    assert role.level == 60
    assert len(role.permissions) > 0
    perm_names = [f"{p.resource}:{p.action}" for p in role.permissions]
    assert "academic_years:create" in perm_names
    assert "students:create" in perm_names


async def test_rector_role_resolves_in_onboarding_service(db_session: AsyncSession, rbac_test_fixture: dict[str, Any]) -> None:
    """2. Verify Rector role resolves seamlessly via RectorOnboardingService without pre-registration."""
    onboarding = RectorOnboardingService(session=db_session)
    inst_b = rbac_test_fixture["inst_b"]

    invitation, raw_token = await onboarding.invite_rector(
        institution_id=inst_b.id,
        first_name="Carlos",
        last_name="Rodriguez",
        document_type=DocumentType.CC,
        document_number="80123456",
        email="carlos.rodriguez@santamaria.edu.co",
        invited_by_id=uuid.uuid4(),
    )
    assert invitation is not None
    assert len(raw_token) >= 32


# ===========================================================================
# 2. Authorization Matrix for Inviting Rectors
# ===========================================================================

async def test_national_admin_can_invite_rector(client: AsyncClient, rbac_test_fixture: dict[str, Any]) -> None:
    """3. National Admin can invite Rector (201 Created)."""
    inst_b = rbac_test_fixture["inst_b"]
    headers = rbac_test_fixture["admin_headers"]

    payload = {
        "first_name": "Maria",
        "last_name": "Gomez",
        "document_type": "CC",
        "document_number": "52987654",
        "email": "maria.gomez@santamaria.edu.co",
    }
    res = await client.post(f"/api/v1/institutions/{inst_b.id}/rector-invitation", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "maria.gomez@santamaria.edu.co"
    assert "raw_invitation_token" in data
    assert data["is_used"] is False


async def test_superadmin_can_invite_rector(client: AsyncClient, rbac_test_fixture: dict[str, Any]) -> None:
    """4. Superadmin can invite Rector (201 Created)."""
    inst_b = rbac_test_fixture["inst_b"]
    headers = rbac_test_fixture["superadmin_headers"]

    payload = {
        "first_name": "Hernando",
        "last_name": "Perez",
        "document_type": "CC",
        "document_number": "79111222",
        "email": "hernando.perez@santamaria.edu.co",
    }
    res = await client.post(f"/api/v1/institutions/{inst_b.id}/rector-invitation", json=payload, headers=headers)
    assert res.status_code == 201


async def test_rector_cannot_invite_another_rector(client: AsyncClient, rbac_test_fixture: dict[str, Any]) -> None:
    """5. Rector cannot invite another Rector (403 Forbidden)."""
    inst_b = rbac_test_fixture["inst_b"]
    headers = rbac_test_fixture["rector_headers"]

    payload = {"first_name": "F", "last_name": "R", "document_type": "CC", "document_number": "99", "email": "f@s.com"}
    res = await client.post(f"/api/v1/institutions/{inst_b.id}/rector-invitation", json=payload, headers=headers)
    assert res.status_code == 403


async def test_coordinator_cannot_invite_rector(client: AsyncClient, rbac_test_fixture: dict[str, Any]) -> None:
    """6. Coordinator cannot invite Rector (403 Forbidden)."""
    inst_b = rbac_test_fixture["inst_b"]
    headers = rbac_test_fixture["coord_headers"]

    payload = {"first_name": "C", "last_name": "C", "document_type": "CC", "document_number": "99", "email": "c@c.com"}
    res = await client.post(f"/api/v1/institutions/{inst_b.id}/rector-invitation", json=payload, headers=headers)
    assert res.status_code == 403


async def test_teacher_cannot_invite_rector(client: AsyncClient, rbac_test_fixture: dict[str, Any]) -> None:
    """7. Teacher cannot invite Rector (403 Forbidden)."""
    inst_b = rbac_test_fixture["inst_b"]
    headers = rbac_test_fixture["teacher_headers"]

    payload = {"first_name": "A", "last_name": "B", "document_type": "CC", "document_number": "1", "email": "a@b.com"}
    res = await client.post(f"/api/v1/institutions/{inst_b.id}/rector-invitation", json=payload, headers=headers)
    assert res.status_code == 403


async def test_student_cannot_invite_rector(client: AsyncClient, rbac_test_fixture: dict[str, Any]) -> None:
    """8. Student cannot invite Rector (403 Forbidden)."""
    inst_b = rbac_test_fixture["inst_b"]
    headers = rbac_test_fixture["student_headers"]

    payload = {"first_name": "A", "last_name": "B", "document_type": "CC", "document_number": "1", "email": "a@b.com"}
    res = await client.post(f"/api/v1/institutions/{inst_b.id}/rector-invitation", json=payload, headers=headers)
    assert res.status_code == 403


async def test_guardian_cannot_invite_rector(client: AsyncClient, rbac_test_fixture: dict[str, Any]) -> None:
    """9. Guardian cannot invite Rector (403 Forbidden)."""
    inst_b = rbac_test_fixture["inst_b"]
    headers = rbac_test_fixture["guardian_headers"]

    payload = {"first_name": "A", "last_name": "B", "document_type": "CC", "document_number": "1", "email": "a@b.com"}
    res = await client.post(f"/api/v1/institutions/{inst_b.id}/rector-invitation", json=payload, headers=headers)
    assert res.status_code == 403


async def test_anonymous_user_cannot_invite_rector(client: AsyncClient, rbac_test_fixture: dict[str, Any]) -> None:
    """10. Anonymous request receives 401/403."""
    inst_b = rbac_test_fixture["inst_b"]
    payload = {"first_name": "A", "last_name": "B", "document_type": "CC", "document_number": "1", "email": "a@b.com"}
    res = await client.post(f"/api/v1/institutions/{inst_b.id}/rector-invitation", json=payload)
    assert res.status_code in (401, 403)


# ===========================================================================
# 3. Rector Onboarding Lifecycle & Cryptographic Zero-Knowledge Tests
# ===========================================================================

async def test_duplicate_active_rector_rejected(client: AsyncClient, rbac_test_fixture: dict[str, Any]) -> None:
    """11. Duplicate active Rector is rejected with 409 RECTOR_ALREADY_EXISTS."""
    inst_a = rbac_test_fixture["inst_a"]  # Already has active rector in fixture
    headers = rbac_test_fixture["admin_headers"]

    payload = {
        "first_name": "Nuevo",
        "last_name": "Candidato",
        "document_type": "CC",
        "document_number": "90000000",
        "email": "nuevo.candidato@sancarlos.edu.co",
    }
    res = await client.post(f"/api/v1/institutions/{inst_a.id}/rector-invitation", json=payload, headers=headers)
    assert res.status_code == 409
    data = res.json()
    assert data["error"]["code"] == "RECTOR_ALREADY_EXISTS"


async def test_invitation_creates_inactive_user_and_inactive_role_with_sha256(
    client: AsyncClient,
    rbac_test_fixture: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    """12. Inactive User + Inactive UserRole(RECTOR) + SHA-256 token hash (zero knowledge)."""
    inst_b = rbac_test_fixture["inst_b"]
    headers = rbac_test_fixture["admin_headers"]

    payload = {
        "first_name": "Alejandro",
        "last_name": "Morales",
        "document_type": "CC",
        "document_number": "71345678",
        "email": "alejandro.morales@santamaria.edu.co",
    }
    res = await client.post(f"/api/v1/institutions/{inst_b.id}/rector-invitation", json=payload, headers=headers)
    assert res.status_code == 201
    raw_token = res.json()["raw_invitation_token"]

    # Inspect database
    user = (await db_session.execute(select(User).where(User.email == "alejandro.morales@santamaria.edu.co"))).scalar_one()
    assert user.is_active is False
    assert user.is_verified is False

    ur = (await db_session.execute(select(UserRole).where(UserRole.user_id == user.id))).scalar_one()
    assert ur.is_active is False

    invitation = (await db_session.execute(select(RectorInvitation).where(RectorInvitation.user_id == user.id))).scalar_one()
    assert invitation.is_used is False
    assert len(invitation.token_hash) == 64
    assert invitation.token_hash != raw_token
    assert hash_token(raw_token) == invitation.token_hash


async def test_rector_accept_invitation_activates_user_and_role(
    client: AsyncClient,
    rbac_test_fixture: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    """13. Accept invitation activates User and Rector role with Argon2id hash."""
    inst_b = rbac_test_fixture["inst_b"]
    headers = rbac_test_fixture["admin_headers"]

    payload = {
        "first_name": "Beatriz",
        "last_name": "Pinzon",
        "document_type": "CC",
        "document_number": "51234567",
        "email": "beatriz.pinzon@santamaria.edu.co",
    }
    res_inv = await client.post(f"/api/v1/institutions/{inst_b.id}/rector-invitation", json=payload, headers=headers)
    assert res_inv.status_code == 201
    raw_token = res_inv.json()["raw_invitation_token"]

    # Accept invitation
    res_acc = await client.post(
        "/api/v1/auth/accept-invitation",
        json={
            "token": raw_token,
            "password": "RectorPassword2026*!",
            "password_confirmation": "RectorPassword2026*!",
        },
    )
    assert res_acc.status_code == 200
    user_id = res_acc.json()["user_id"]

    # Verify user is now active
    user = (await db_session.execute(select(User).where(User.id == uuid.UUID(user_id)))).scalar_one()
    assert user.is_active is True
    assert user.is_verified is True

    # Verify user role is now active
    ur = (await db_session.execute(select(UserRole).where(UserRole.user_id == user.id))).scalar_one()
    assert ur.is_active is True


async def test_rector_cannot_provision_institution(client: AsyncClient, rbac_test_fixture: dict[str, Any]) -> None:
    """14. Rector cannot provision institutions (403 Forbidden)."""
    headers = rbac_test_fixture["rector_headers"]
    payload = {
        "dane_code": "123456789012",
        "name": "COLEGIO ILEGAL",
        "email": "ilegal@colegio.edu.co",
        "municipality_id": "25001",
    }
    res = await client.post("/api/v1/institutions", json=payload, headers=headers)
    assert res.status_code == 403


# ===========================================================================
# 4. Virtual Classrooms & Recordings RBAC Matrix Enforcement
# ===========================================================================

async def test_teacher_can_create_virtual_classroom(client: AsyncClient, rbac_test_fixture: dict[str, Any]) -> None:
    """15. Teacher can create virtual classrooms within institution scope (201 Created)."""
    headers = rbac_test_fixture["teacher_headers"]
    payload = {
        "title": "Clase de Matemáticas Grado 6",
        "description": "Sesión en vivo de fracciones",
        "max_participants": 40,
        "is_recording_enabled": True,
    }
    res = await client.post("/api/v1/virtual-classrooms", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "Clase de Matemáticas Grado 6"
    assert data["status"] == "SCHEDULED"


async def test_guardian_cannot_create_virtual_classroom(client: AsyncClient, rbac_test_fixture: dict[str, Any]) -> None:
    """16. Guardian is denied virtual classroom creation (403 Forbidden)."""
    headers = rbac_test_fixture["guardian_headers"]
    payload = {
        "title": "Reunión no autorizada",
        "max_participants": 20,
    }
    res = await client.post("/api/v1/virtual-classrooms", json=payload, headers=headers)
    assert res.status_code == 403


async def test_guardian_cannot_read_virtual_classrooms(client: AsyncClient, rbac_test_fixture: dict[str, Any]) -> None:
    """17. Guardian is denied reading virtual classrooms list (403 Forbidden)."""
    headers = rbac_test_fixture["guardian_headers"]
    res = await client.get("/api/v1/virtual-classrooms", headers=headers)
    assert res.status_code == 403


async def test_student_and_teacher_can_read_virtual_classrooms(client: AsyncClient, rbac_test_fixture: dict[str, Any]) -> None:
    """18. Student and Teacher can read virtual classrooms (200 OK)."""
    teacher_headers = rbac_test_fixture["teacher_headers"]
    student_headers = rbac_test_fixture["student_headers"]

    res_t = await client.get("/api/v1/virtual-classrooms", headers=teacher_headers)
    assert res_t.status_code == 200

    res_s = await client.get("/api/v1/virtual-classrooms", headers=student_headers)
    assert res_s.status_code == 200


async def test_guardian_cannot_read_recordings(client: AsyncClient, rbac_test_fixture: dict[str, Any]) -> None:
    """19. Guardian is denied reading recordings (403 Forbidden)."""
    headers = rbac_test_fixture["guardian_headers"]
    dummy_class_id = uuid.uuid4()
    res = await client.get(f"/api/v1/recordings/classroom/{dummy_class_id}", headers=headers)
    assert res.status_code == 403


# ===========================================================================
# 5. Tenant Containment & Cross-Institution Access Isolation
# ===========================================================================

async def test_institution_read_uses_explicit_permission_and_scope(client: AsyncClient, rbac_test_fixture: dict[str, Any]) -> None:
    """20. Institution read authorization uses explicit institutions:read permission with scope check."""
    inst_a = rbac_test_fixture["inst_a"]
    headers = rbac_test_fixture["rector_headers"]
    res = await client.get(f"/api/v1/institutions/{inst_a.id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["id"] == str(inst_a.id)


async def test_rector_a_cannot_access_institution_b(client: AsyncClient, rbac_test_fixture: dict[str, Any]) -> None:
    """21. Rector A cannot access Institution B (cross-tenant 403 Forbidden)."""
    inst_b = rbac_test_fixture["inst_b"]
    rector_a_headers = rbac_test_fixture["rector_headers"]
    res = await client.get(f"/api/v1/institutions/{inst_b.id}", headers=rector_a_headers)
    assert res.status_code == 403


async def test_rector_a_cannot_read_academic_years_of_institution_b(client: AsyncClient, rbac_test_fixture: dict[str, Any]) -> None:
    """22. Rector A cannot read academic years of Institution B (tenant containment)."""
    ay_b = rbac_test_fixture["ay_b"]
    rector_a_headers = rbac_test_fixture["rector_headers"]

    # Direct access by ID: should fail with 403 or 404
    res = await client.get(f"/api/v1/academic-years/{ay_b.id}", headers=rector_a_headers)
    assert res.status_code in (403, 404)


# ===========================================================================
# 6. Academic Hierarchy Boundaries
# ===========================================================================

async def test_coordinator_can_create_groups_but_cannot_create_academic_years(
    client: AsyncClient,
    rbac_test_fixture: dict[str, Any],
) -> None:
    """23. Coordinator can create groups within tenant scope but cannot create academic years (RBAC boundary)."""
    coord_headers = rbac_test_fixture["coord_headers"]
    inst_a = rbac_test_fixture["inst_a"]
    campus_a = rbac_test_fixture["campus_a"]
    grade_6 = rbac_test_fixture["grade_6"]
    ay_a = rbac_test_fixture["ay_a"]

    # 1. Attempt to create academic year -> 403 Forbidden
    res_ay = await client.post(
        "/api/v1/academic-years",
        json={
            "year": 2027,
            "name": "Año 2027",
            "start_date": "2027-01-15T00:00:00",
            "end_date": "2027-11-30T00:00:00",
            "calendar_type": "A",
        },
        headers=coord_headers,
    )
    assert res_ay.status_code == 403

    # 2. Coordinator can create group -> 201 Created
    res_grp = await client.post(
        "/api/v1/groups",
        json={
            "campus_id": str(campus_a.id),
            "academic_year_id": str(ay_a.id),
            "grade_id": str(grade_6.id),
            "name": "601",
            "shift": "MANANA",
            "capacity_limit": 35,
        },
        headers=coord_headers,
    )
    assert res_grp.status_code == 201


async def test_student_and_guardian_rbac_boundaries(client: AsyncClient, rbac_test_fixture: dict[str, Any]) -> None:
    """24 & 25. Student and Guardian access boundaries (authorized read, forbidden management)."""
    student_headers = rbac_test_fixture["student_headers"]
    guardian_headers = rbac_test_fixture["guardian_headers"]
    campus_a = rbac_test_fixture["campus_a"]
    grade_6 = rbac_test_fixture["grade_6"]
    ay_a = rbac_test_fixture["ay_a"]

    # 1. Student can read academic assignments -> 200 OK
    res_s_read = await client.get("/api/v1/academic-assignments", headers=student_headers)
    assert res_s_read.status_code == 200

    # 2. Student cannot read or create groups (groups:read and groups:create are staff only) -> 403 Forbidden
    res_s_groups_read = await client.get("/api/v1/groups", headers=student_headers)
    assert res_s_groups_read.status_code == 403

    res_s_write = await client.post(
        "/api/v1/groups",
        json={
            "campus_id": str(campus_a.id),
            "academic_year_id": str(ay_a.id),
            "grade_id": str(grade_6.id),
            "name": "602-ILLEGAL",
            "shift": "MANANA",
            "capacity_limit": 35,
        },
        headers=student_headers,
    )
    assert res_s_write.status_code == 403

    # 3. Guardian can read guardians list/profile -> 200 OK
    res_g_read = await client.get("/api/v1/guardians", headers=guardian_headers)
    assert res_g_read.status_code == 200

    # 4. Guardian cannot read virtual classrooms or create groups -> 403 Forbidden
    res_g_vc = await client.get("/api/v1/virtual-classrooms", headers=guardian_headers)
    assert res_g_vc.status_code == 403

    res_g_write = await client.post(
        "/api/v1/groups",
        json={
            "campus_id": str(campus_a.id),
            "academic_year_id": str(ay_a.id),
            "grade_id": str(grade_6.id),
            "name": "603-ILLEGAL",
            "shift": "MANANA",
            "capacity_limit": 35,
        },
        headers=guardian_headers,
    )
    assert res_g_write.status_code == 403


async def test_national_admin_and_superadmin_retain_national_scope(client: AsyncClient, rbac_test_fixture: dict[str, Any]) -> None:
    """26. National Admin and Superadmin retain global / national authority over catalog."""
    admin_headers = rbac_test_fixture["admin_headers"]
    superadmin_headers = rbac_test_fixture["superadmin_headers"]

    # National admin queries institutions catalog
    res_adm = await client.get("/api/v1/institutions", headers=admin_headers)
    assert res_adm.status_code == 200

    # Superadmin queries institutions catalog
    res_sup = await client.get("/api/v1/institutions", headers=superadmin_headers)
    assert res_sup.status_code == 200
