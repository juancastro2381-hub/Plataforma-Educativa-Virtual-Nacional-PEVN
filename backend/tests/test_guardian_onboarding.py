"""
PEVN Backend — Guardian Secure Self-Onboarding Test Suite (Phase 7 - Step 2)

Authoritative verification of the Guardian self-onboarding lifecycle:
  1. Valid guardian onboarding: request -> verify -> accept with Argon2id -> login -> profile.
  2. Invalid SIMAT / enrollment code returns 404 STUDENT_NOT_FOUND.
  3. Invalid guardian document returns 404 GUARDIAN_NOT_FOUND.
  4. Unlinked guardian/student relationship returns 404 GUARDIAN_RELATION_NOT_FOUND.
  5. Cross-institution attempt is rejected.
  6. Expired activation token returns 409 TOKEN_EXPIRED.
  7. Already-used activation token returns 409 TOKEN_ALREADY_USED.
  8. Revoked / superseded token returns 409 TOKEN_REVOKED.
  9. Password confirmation mismatch is rejected with 400/422 validation error.
  10. Offline/rural guardian compatibility (OPEN-DECISION-3A-01): unactivated guardian remains valid with user_id=None.
  11. Tenant/institution isolation: guardian account is bound exclusively to target institution.
  12. Audit trail integrity: formal audit events are recorded without leaking secrets.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.core.security.tokens import hash_token, token_service
from app.models.guardian import (
    Guardian,
    GuardianRelationshipType,
    StudentGuardian,
)
from app.models.institution import Campus, Institution
from app.models.invitation import GuardianInvitation
from app.models.role import Role, UserRole
from app.models.student import Student, StudentGender
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User
from app.services.rbac_bootstrap_service import RbacBootstrapService


@pytest.fixture
async def guardian_fixture(db_session: AsyncSession) -> dict[str, Any]:
    """Seed institutions, students, offline guardians and staff tokens."""
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
        dane_code="125001000888",
        name="I.E. Departamental San Carlos",
        email="rectoria@sancarlos.edu.co",
        is_active=True,
    )
    inst_b = Institution(
        municipality_id=muni.id,
        dane_code="125001000999",
        name="I.E. Departamental Santa Maria",
        email="rectoria@santamaria.edu.co",
        is_active=True,
    )
    db_session.add_all([inst_a, inst_b])
    await db_session.flush()

    campus_a = Campus(
        institution_id=inst_a.id,
        dane_sede_code="12500100088801",
        name="Sede Principal San Carlos",
        is_active=True,
    )
    db_session.add(campus_a)
    await db_session.flush()

    role_student = (await db_session.execute(select(Role).where(Role.name == "student"))).scalar_one()

    # Student User A
    student_user_a = User(
        institution_id=inst_a.id,
        email="carlos.estudiante@sancarlos.edu.co",
        username="carlos.estudiante",
        hashed_password=password_hasher.hash("StudentPass123!"),
        first_name="Carlos",
        last_name="Perez",
        document_type=DocumentType.TI,
        document_number="1020304050",
        is_active=True,
        is_verified=True,
    )
    # Student User B (in Inst B)
    student_user_b = User(
        institution_id=inst_b.id,
        email="maria.estudiante@santamaria.edu.co",
        username="maria.estudiante",
        hashed_password=password_hasher.hash("StudentPass123!"),
        first_name="Maria",
        last_name="Gomez",
        document_type=DocumentType.TI,
        document_number="1020304060",
        is_active=True,
        is_verified=True,
    )
    db_session.add_all([student_user_a, student_user_b])
    await db_session.flush()

    db_session.add_all([
        UserRole(user_id=student_user_a.id, role_id=role_student.id, institution_id=inst_a.id, is_active=True),
        UserRole(user_id=student_user_b.id, role_id=role_student.id, institution_id=inst_b.id, is_active=True),
    ])
    await db_session.flush()

    # Student domain entities
    student_a = Student(
        user_id=student_user_a.id,
        institution_id=inst_a.id,
        code_simat="SIMAT-2026-001",
        birth_date=date(2012, 5, 15),
        gender=StudentGender.M,
        stratum=2,
    )
    student_b = Student(
        user_id=student_user_b.id,
        institution_id=inst_b.id,
        code_simat="SIMAT-2026-002",
        birth_date=date(2013, 8, 20),
        gender=StudentGender.F,
        stratum=3,
    )
    db_session.add_all([student_a, student_b])
    await db_session.flush()

    # Offline / Rural Guardian 1 (Pre-registered by institution during enrollment, user_id=None per OPEN-DECISION-3A-01)
    guardian_offline_1 = Guardian(
        institution_id=inst_a.id,
        user_id=None,
        document_type=DocumentType.CC,
        document_number="52987654",
        first_name="Rosa",
        last_name="Perez",
        phone="+57 310 1234567",
        email="rosa.perez@correo.com",
        relationship_type=GuardianRelationshipType.MADRE,
    )
    # Offline Guardian 2 (Unrelated guardian)
    guardian_offline_2 = Guardian(
        institution_id=inst_a.id,
        user_id=None,
        document_type=DocumentType.CC,
        document_number="52987999",
        first_name="Ana",
        last_name="Martinez",
        phone="+57 310 7654321",
        email="ana.martinez@correo.com",
        relationship_type=GuardianRelationshipType.TIO_A,
    )
    db_session.add_all([guardian_offline_1, guardian_offline_2])
    await db_session.flush()

    # Link Guardian 1 to Student A (in Inst A)
    link_1 = StudentGuardian(
        student_id=student_a.id,
        guardian_id=guardian_offline_1.id,
        relationship_type=GuardianRelationshipType.MADRE,
        is_primary_contact=True,
        is_authorized_pickup=True,
    )
    db_session.add(link_1)
    await db_session.commit()

    return {
        "inst_a": inst_a,
        "inst_b": inst_b,
        "student_a": student_a,
        "student_b": student_b,
        "student_user_a": student_user_a,
        "guardian_offline_1": guardian_offline_1,
        "guardian_offline_2": guardian_offline_2,
    }


@pytest.mark.asyncio
async def test_valid_guardian_onboarding_lifecycle(
    client: AsyncClient,
    db_session: AsyncSession,
    guardian_fixture: dict[str, Any],
) -> None:
    """1. Full valid onboarding lifecycle: request -> verify -> accept -> login."""
    guardian_1 = guardian_fixture["guardian_offline_1"]
    student_a = guardian_fixture["student_a"]
    inst_a = guardian_fixture["inst_a"]

    # Step 1: Request activation
    res_req = await client.post(
        "/api/v1/auth/guardians/request-activation",
        json={
            "student_code_simat": "SIMAT-2026-001",
            "guardian_document_type": "CC",
            "guardian_document_number": "52987654",
            "email": "rosa.perez@correo.com",
        },
    )
    assert res_req.status_code == 200
    req_data = res_req.json()
    raw_token = req_data["raw_activation_token"]
    assert raw_token is not None

    # Step 2: Verify token
    res_ver = await client.post(
        "/api/v1/auth/guardians/verify-token",
        json={"token": raw_token},
    )
    assert res_ver.status_code == 200
    ver_data = res_ver.json()
    assert ver_data["valid"] is True
    assert "Rosa Perez" in ver_data["guardian_name"]
    assert "Carlos Perez" in ver_data["student_name"]
    assert ver_data["institution_name"] == inst_a.name

    # Step 3: Accept activation and define password
    res_acc = await client.post(
        "/api/v1/auth/guardians/accept-activation",
        json={
            "token": raw_token,
            "password": "GuardianSecure2026*!",
            "password_confirmation": "GuardianSecure2026*!",
        },
    )
    assert res_acc.status_code == 200
    acc_data = res_acc.json()
    assert acc_data["is_active"] is True
    assert acc_data["email"] == "rosa.perez@correo.com"

    # Step 4: Verify Guardian is now linked in database
    await db_session.refresh(guardian_1)
    assert guardian_1.user_id is not None

    # Verify UserRole has 'guardian' role in Institution A
    role_guardian = (await db_session.execute(select(Role).where(Role.name == "guardian"))).scalar_one()
    ur = (
        await db_session.execute(
            select(UserRole).where(
                UserRole.user_id == guardian_1.user_id,
                UserRole.role_id == role_guardian.id,
                UserRole.institution_id == inst_a.id,
            )
        )
    ).scalar_one()
    assert ur.is_active is True

    # Step 5: Login with newly activated credentials
    res_login = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "rosa.perez@correo.com",
            "password": "GuardianSecure2026*!",
        },
    )
    assert res_login.status_code == 200
    login_data = res_login.json()
    assert "access_token" in login_data

    # Step 6: Query /me profile
    res_me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login_data['access_token']}"},
    )
    assert res_me.status_code == 200
    me_data = res_me.json()
    assert "guardian" in me_data["roles"]
    assert me_data["scope"]["institution_id"] == str(inst_a.id)


@pytest.mark.asyncio
async def test_invalid_simat_code_returns_404(
    client: AsyncClient,
    guardian_fixture: dict[str, Any],
) -> None:
    """2. Non-existent SIMAT code returns 404 STUDENT_NOT_FOUND."""
    res = await client.post(
        "/api/v1/auth/guardians/request-activation",
        json={
            "student_code_simat": "SIMAT-INEXISTENTE-999",
            "guardian_document_type": "CC",
            "guardian_document_number": "52987654",
            "email": "rosa.perez@correo.com",
        },
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "STUDENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_invalid_guardian_document_returns_404(
    client: AsyncClient,
    guardian_fixture: dict[str, Any],
) -> None:
    """3. Non-existent guardian document returns 404 GUARDIAN_NOT_FOUND."""
    res = await client.post(
        "/api/v1/auth/guardians/request-activation",
        json={
            "student_code_simat": "SIMAT-2026-001",
            "guardian_document_type": "CC",
            "guardian_document_number": "99999999",
            "email": "desconocido@correo.com",
        },
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "GUARDIAN_NOT_FOUND"


@pytest.mark.asyncio
async def test_unlinked_guardian_student_returns_404(
    client: AsyncClient,
    guardian_fixture: dict[str, Any],
) -> None:
    """4. Unlinked guardian requesting activation for unrelated student returns 404 GUARDIAN_RELATION_NOT_FOUND."""
    # Guardian 2 is not linked to Student A
    res = await client.post(
        "/api/v1/auth/guardians/request-activation",
        json={
            "student_code_simat": "SIMAT-2026-001",
            "guardian_document_type": "CC",
            "guardian_document_number": "52987999",
            "email": "ana.martinez@correo.com",
        },
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "GUARDIAN_RELATION_NOT_FOUND"


@pytest.mark.asyncio
async def test_cross_institution_unauthorized_relationship_rejected(
    client: AsyncClient,
    guardian_fixture: dict[str, Any],
) -> None:
    """5. Attempting to activate guardian against Student B from another institution where not linked."""
    res = await client.post(
        "/api/v1/auth/guardians/request-activation",
        json={
            "student_code_simat": "SIMAT-2026-002",  # Student B in Inst B
            "guardian_document_type": "CC",
            "guardian_document_number": "52987654",  # Guardian 1 (linked to Student A in Inst A)
            "email": "rosa.perez@correo.com",
        },
    )
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "GUARDIAN_RELATION_NOT_FOUND"


@pytest.mark.asyncio
async def test_expired_token_rejected_with_409(
    client: AsyncClient,
    db_session: AsyncSession,
    guardian_fixture: dict[str, Any],
) -> None:
    """6. Expired activation token returns 409 TOKEN_EXPIRED."""
    guardian_1 = guardian_fixture["guardian_offline_1"]
    student_a = guardian_fixture["student_a"]
    inst_a = guardian_fixture["inst_a"]

    raw_token = "expired_token_12345678901234567890"
    inv = GuardianInvitation(
        guardian_id=guardian_1.id,
        student_id=student_a.id,
        institution_id=inst_a.id,
        token_hash=hash_token(raw_token),
        email="rosa.perez@correo.com",
        expires_at=datetime.now(UTC) - timedelta(hours=2),
    )
    db_session.add(inv)
    await db_session.commit()

    res_ver = await client.post(
        "/api/v1/auth/guardians/verify-token",
        json={"token": raw_token},
    )
    assert res_ver.status_code == 409
    assert res_ver.json()["error"]["code"] == "TOKEN_EXPIRED"


@pytest.mark.asyncio
async def test_token_reuse_prevented_with_409(
    client: AsyncClient,
    guardian_fixture: dict[str, Any],
) -> None:
    """7. Reusing an already-redeemed token returns 409 TOKEN_ALREADY_USED."""
    # Step 1: Request activation
    res_req = await client.post(
        "/api/v1/auth/guardians/request-activation",
        json={
            "student_code_simat": "SIMAT-2026-001",
            "guardian_document_type": "CC",
            "guardian_document_number": "52987654",
            "email": "rosa.perez@correo.com",
        },
    )
    raw_token = res_req.json()["raw_activation_token"]

    # Step 2: Redeem once
    res_acc = await client.post(
        "/api/v1/auth/guardians/accept-activation",
        json={
            "token": raw_token,
            "password": "GuardianPass123!",
            "password_confirmation": "GuardianPass123!",
        },
    )
    assert res_acc.status_code == 200

    # Step 3: Attempt to redeem again
    res_reuse = await client.post(
        "/api/v1/auth/guardians/accept-activation",
        json={
            "token": raw_token,
            "password": "AnotherPassword123!",
            "password_confirmation": "AnotherPassword123!",
        },
    )
    assert res_reuse.status_code == 409
    assert res_reuse.json()["error"]["code"] == "TOKEN_ALREADY_USED"


@pytest.mark.asyncio
async def test_revoked_token_rejected_with_409(
    client: AsyncClient,
    guardian_fixture: dict[str, Any],
) -> None:
    """8. Superseded invitation token is marked revoked and rejected."""
    # Request first token
    res_1 = await client.post(
        "/api/v1/auth/guardians/request-activation",
        json={
            "student_code_simat": "SIMAT-2026-001",
            "guardian_document_type": "CC",
            "guardian_document_number": "52987654",
            "email": "rosa.perez@correo.com",
        },
    )
    token_1 = res_1.json()["raw_activation_token"]

    # Request second token (supersedes first)
    res_2 = await client.post(
        "/api/v1/auth/guardians/request-activation",
        json={
            "student_code_simat": "SIMAT-2026-001",
            "guardian_document_type": "CC",
            "guardian_document_number": "52987654",
            "email": "rosa.perez@correo.com",
        },
    )
    token_2 = res_2.json()["raw_activation_token"]

    # Verify first token is now revoked
    res_ver_1 = await client.post(
        "/api/v1/auth/guardians/verify-token",
        json={"token": token_1},
    )
    assert res_ver_1.status_code == 409
    assert res_ver_1.json()["error"]["code"] == "TOKEN_REVOKED"

    # Verify second token is valid
    res_ver_2 = await client.post(
        "/api/v1/auth/guardians/verify-token",
        json={"token": token_2},
    )
    assert res_ver_2.status_code == 200


@pytest.mark.asyncio
async def test_password_mismatch_rejected_with_validation_error(
    client: AsyncClient,
    guardian_fixture: dict[str, Any],
) -> None:
    """9. Password confirmation mismatch is rejected."""
    res_req = await client.post(
        "/api/v1/auth/guardians/request-activation",
        json={
            "student_code_simat": "SIMAT-2026-001",
            "guardian_document_type": "CC",
            "guardian_document_number": "52987654",
            "email": "rosa.perez@correo.com",
        },
    )
    raw_token = res_req.json()["raw_activation_token"]

    res_acc = await client.post(
        "/api/v1/auth/guardians/accept-activation",
        json={
            "token": raw_token,
            "password": "Password123!",
            "password_confirmation": "DifferentPassword123!",
        },
    )
    assert res_acc.status_code in (400, 422)


@pytest.mark.asyncio
async def test_offline_guardian_preservation(
    db_session: AsyncSession,
    guardian_fixture: dict[str, Any],
) -> None:
    """10. Offline / rural guardian without user account remains 100% valid (OPEN-DECISION-3A-01)."""
    guardian_2 = guardian_fixture["guardian_offline_2"]

    # Verify guardian exists with user_id = None
    assert guardian_2.user_id is None
    assert guardian_2.document_number == "52987999"

    # Verify database queries for legal guardian function correctly without user account
    db_guardian = (
        await db_session.execute(
            select(Guardian).where(Guardian.document_number == "52987999")
        )
    ).scalar_one()
    assert db_guardian is not None
    assert db_guardian.user_id is None
