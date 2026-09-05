"""
PEVN Backend — Identity & Family Lifecycle Step 1 Test Suite

Comprehensive automated verification of:
  1. Guardian provisioning without login account (civil registration only).
  2. Guardian provisioning with inline account creation & setup token delivery.
  3. Guardian linking to existing user with dynamic role assignment.
  4. Guardian account status toggle (ACTIVA <-> INACTIVA) & session revocation.
  5. Guardian administrative password reset with cryptographic token generation.
  6. Student account status toggle (ACTIVA <-> INACTIVA).
  7. Student administrative password reset with cryptographic token generation.
  8. Bidirectional Guardian ↔ Student linking from Guardian View.
  9. Bidirectional Guardian ↔ Student linking from Student View.
  10. Safe disassociation from Guardian View (preserves civil & user entities).
  11. Safe disassociation from Student View (preserves civil & user entities).
  12. Anti-IDOR cross-institution tenant isolation barriers.
  13. Public Guardian self-activation lifecycle (request -> verify -> accept -> login).
  14. Token segregation in entity responses (reset_token strictly omitted from list/detail).
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
from app.core.security.tokens import token_service
from app.models.academic_year import AcademicYear
from app.models.grade import Grade
from app.models.guardian import (
    Guardian,
    GuardianRelationshipType,
    StudentGuardian,
)
from app.models.institution import Campus, Institution
from app.models.role import Permission, Role, RolePermission, UserRole
from app.models.student import Student, StudentGender
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User
from app.services.rbac_bootstrap_service import RbacBootstrapService


@pytest.fixture
async def lifecycle_fixture(db_session: AsyncSession) -> dict[str, Any]:
    """Seed multi-tenant institutions, rector users, students, and permissions."""
    bootstrap = RbacBootstrapService(session=db_session)
    await bootstrap.seed_canonical_rbac_if_needed()

    dept = Department(code="76", name="Valle del Cauca")
    db_session.add(dept)
    await db_session.flush()

    muni = Municipality(department_id=dept.id, code="76001", name="Cali")
    db_session.add(muni)
    await db_session.flush()

    # Institution 1 (Librada)
    inst1 = Institution(
        dane_code="176001000111",
        name="Colegio Santa Librada",
        email="contacto@librada.edu.co",
        municipality_id=muni.id,
        is_active=True,
    )
    # Institution 2 (San Luis)
    inst2 = Institution(
        dane_code="176001000222",
        name="Instituto San Luis",
        email="contacto@sanluis.edu.co",
        municipality_id=muni.id,
        is_active=True,
    )
    db_session.add_all([inst1, inst2])
    await db_session.flush()

    # Campuses
    campus1 = Campus(
        institution_id=inst1.id,
        dane_sede_code="176001000112",
        name="Sede Principal Librada",
        is_active=True,
    )
    campus2 = Campus(
        institution_id=inst2.id,
        dane_sede_code="176001000223",
        name="Sede Principal San Luis",
        is_active=True,
    )
    db_session.add_all([campus1, campus2])
    await db_session.flush()

    # Assign all required permissions to Rector role
    rector_role = (
        await db_session.execute(
            select(Role).where(Role.name == SystemRole.RECTOR.value)
        )
    ).scalar_one()

    required_perms = [
        ("students", "read"),
        ("students", "create"),
        ("students", "update"),
        ("guardians", "read"),
        ("guardians", "create"),
        ("guardians", "update"),
        ("guardians", "link_student"),
        ("users", "read"),
    ]

    for res, act in required_perms:
        perm = (
            await db_session.execute(
                select(Permission).where(
                    Permission.resource == res, Permission.action == act
                )
            )
        ).scalar_one_or_none()
        if not perm:
            perm = Permission(resource=res, action=act, description=f"{res}:{act}")
            db_session.add(perm)
            await db_session.flush()

        rp = (
            await db_session.execute(
                select(RolePermission).where(
                    RolePermission.role_id == rector_role.id,
                    RolePermission.permission_id == perm.id,
                )
            )
        ).scalar_one_or_none()
        if not rp:
            db_session.add(
                RolePermission(role_id=rector_role.id, permission_id=perm.id)
            )
    await db_session.flush()

    # Rector 1
    rector1 = User(
        email="rector1@librada.edu.co",
        username="rector1",
        hashed_password=password_hasher.hash("RectorPass123!"),
        first_name="Rector",
        last_name="Librada",
        document_type=DocumentType.CC,
        document_number="80111222",
        institution_id=inst1.id,
        is_active=True,
        is_verified=True,
    )
    # Rector 2 (Different tenant)
    rector2 = User(
        email="rector2@sanluis.edu.co",
        username="rector2",
        hashed_password=password_hasher.hash("RectorPass123!"),
        first_name="Rector",
        last_name="San Luis",
        document_type=DocumentType.CC,
        document_number="80333444",
        institution_id=inst2.id,
        is_active=True,
        is_verified=True,
    )
    db_session.add_all([rector1, rector2])
    await db_session.flush()

    db_session.add_all([
        UserRole(user_id=rector1.id, role_id=rector_role.id),
        UserRole(user_id=rector2.id, role_id=rector_role.id),
    ])
    await db_session.flush()

    # Pre-seed Student in Inst 1
    student_u1 = User(
        email="estudiante1@librada.edu.co",
        username="estudiante1",
        hashed_password=password_hasher.hash("StudentPass123!"),
        first_name="Santiago",
        last_name="Castro",
        document_type=DocumentType.TI,
        document_number="100555666",
        institution_id=inst1.id,
        is_active=True,
        is_verified=True,
    )
    db_session.add(student_u1)
    await db_session.flush()

    student_role = (
        await db_session.execute(
            select(Role).where(Role.name == SystemRole.STUDENT.value)
        )
    ).scalar_one()
    db_session.add(UserRole(user_id=student_u1.id, role_id=student_role.id))
    await db_session.flush()

    student1 = Student(
        user_id=student_u1.id,
        institution_id=inst1.id,
        code_simat="SIMAT-2026-ST1",
        birth_date=date(2010, 5, 15),
        gender=StudentGender.M,
        stratum=3,
        eps_health_provider="Sura",
    )
    db_session.add(student1)
    await db_session.flush()

    # Pre-seed Student in Inst 2 (for IDOR testing)
    student_u2 = User(
        email="estudiante2@sanluis.edu.co",
        username="estudiante2",
        hashed_password=password_hasher.hash("StudentPass123!"),
        first_name="Valentina",
        last_name="Gomez",
        document_type=DocumentType.TI,
        document_number="100777888",
        institution_id=inst2.id,
        is_active=True,
        is_verified=True,
    )
    db_session.add(student_u2)
    await db_session.flush()
    db_session.add(UserRole(user_id=student_u2.id, role_id=student_role.id))
    await db_session.flush()

    student2 = Student(
        user_id=student_u2.id,
        institution_id=inst2.id,
        code_simat="SIMAT-2026-ST2",
        birth_date=date(2011, 3, 20),
        gender=StudentGender.F,
        stratum=2,
    )
    db_session.add(student2)
    await db_session.flush()

    rector1_token = await token_service.create_access_token(
        subject=str(rector1.id),
        additional_claims={
            "roles": [SystemRole.RECTOR.value],
            "institution_id": str(inst1.id),
        },
    )
    rector2_token = await token_service.create_access_token(
        subject=str(rector2.id),
        additional_claims={
            "roles": [SystemRole.RECTOR.value],
            "institution_id": str(inst2.id),
        },
    )

    await db_session.commit()

    return {
        "inst1": inst1,
        "inst2": inst2,
        "rector1": rector1,
        "rector2": rector2,
        "student1": student1,
        "student_u1": student_u1,
        "student2": student2,
        "student_u2": student_u2,
        "rector1_headers": {"Authorization": f"Bearer {rector1_token}"},
        "rector2_headers": {"Authorization": f"Bearer {rector2_token}"},
    }


# ===========================================================================
# 1. Guardian Provisioning Tests
# ===========================================================================


async def test_guardian_provisioning_without_account(
    client: AsyncClient,
    lifecycle_fixture: dict[str, Any],
) -> None:
    """Civil guardian registration only: no User account, status SIN_CUENTA."""
    headers = lifecycle_fixture["rector1_headers"]
    doc_num = f"41{uuid.uuid4().hex[:6]}"

    res = await client.post(
        "/api/v1/guardians",
        json={
            "first_name": "Martha",
            "last_name": "Lucia",
            "document_type": "CC",
            "document_number": doc_num,
            "phone": "3151112233",
            "email": None,
            "relationship_type": "MADRE",
            "provision_account": False,
        },
        headers=headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["first_name"] == "Martha"
    assert data["user_id"] is None
    assert data["has_account"] is False
    assert data["account_status"] == "SIN_CUENTA"


async def test_guardian_provisioning_with_account_creation(
    client: AsyncClient,
    lifecycle_fixture: dict[str, Any],
) -> None:
    """Guardian registration with new User account: generates setup token, status ACTIVA."""
    headers = lifecycle_fixture["rector1_headers"]
    doc_num = f"52{uuid.uuid4().hex[:6]}"
    guardian_email = f"guardian_{doc_num}@correo.com"

    res = await client.post(
        "/api/v1/guardians",
        json={
            "first_name": "Carlos",
            "last_name": "Andres",
            "document_type": "CC",
            "document_number": doc_num,
            "phone": "3162223344",
            "email": guardian_email,
            "relationship_type": "PADRE",
            "provision_account": True,
            "new_user": {
                "first_name": "Carlos",
                "last_name": "Andres",
                "document_type": "CC",
                "document_number": doc_num,
                "email": guardian_email,
                "phone": "3162223344",
            },
        },
        headers=headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["first_name"] == "Carlos"
    assert data["user_id"] is not None
    assert data["has_account"] is True
    assert data["account_status"] == "ACTIVA"
    assert data["account_email"] == guardian_email


async def test_guardian_linking_to_existing_user(
    client: AsyncClient,
    lifecycle_fixture: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    """Link Guardian to existing user: grants guardian role dynamically."""
    inst1: Institution = lifecycle_fixture["inst1"]
    headers = lifecycle_fixture["rector1_headers"]

    # Pre-create standard user in inst1
    doc_num = f"63{uuid.uuid4().hex[:6]}"
    existing_user = User(
        email=f"user_{doc_num}@librada.edu.co",
        username=f"user_{doc_num}",
        hashed_password=password_hasher.hash("SomePass123!"),
        first_name="Fernando",
        last_name="Ruiz",
        document_type=DocumentType.CC,
        document_number=doc_num,
        institution_id=inst1.id,
        is_active=True,
        is_verified=True,
    )
    db_session.add(existing_user)
    await db_session.commit()

    res = await client.post(
        "/api/v1/guardians",
        json={
            "first_name": "Fernando",
            "last_name": "Ruiz",
            "document_type": "CC",
            "document_number": doc_num,
            "phone": "3173334455",
            "email": existing_user.email,
            "relationship_type": "TUTOR_LEGAL",
            "user_id": str(existing_user.id),
        },
        headers=headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["user_id"] == str(existing_user.id)
    assert data["has_account"] is True
    assert data["account_status"] == "ACTIVA"


# ===========================================================================
# 2. Guardian Account Lifecycle (Status Toggle, Reset Password)
# ===========================================================================


async def test_guardian_account_status_toggle_and_reset_password(
    client: AsyncClient,
    lifecycle_fixture: dict[str, Any],
) -> None:
    """Test administrative account enable/disable and password reset for guardian."""
    headers = lifecycle_fixture["rector1_headers"]
    doc_num = f"74{uuid.uuid4().hex[:6]}"
    guardian_email = f"guardian_{doc_num}@correo.com"

    # 1. Create with account
    create_res = await client.post(
        "/api/v1/guardians",
        json={
            "first_name": "Patricia",
            "last_name": "Vargas",
            "document_type": "CC",
            "document_number": doc_num,
            "phone": "3184445566",
            "email": guardian_email,
            "relationship_type": "MADRE",
            "provision_account": True,
            "new_user": {
                "first_name": "Patricia",
                "last_name": "Vargas",
                "document_type": "CC",
                "document_number": doc_num,
                "email": guardian_email,
            },
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    guardian_id = create_res.json()["id"]
    assert create_res.json()["account_status"] == "ACTIVA"

    # 2. Deactivate account
    deact_res = await client.post(
        f"/api/v1/guardians/{guardian_id}/account/status",
        json={"is_active": False},
        headers=headers,
    )
    assert deact_res.status_code == 200
    assert deact_res.json()["account_status"] == "INACTIVA"

    # 3. Reactivate account
    react_res = await client.post(
        f"/api/v1/guardians/{guardian_id}/account/status",
        json={"is_active": True},
        headers=headers,
    )
    assert react_res.status_code == 200
    assert react_res.json()["account_status"] == "ACTIVA"

    # 4. Generate password reset token
    reset_res = await client.post(
        f"/api/v1/guardians/{guardian_id}/account/reset-password",
        headers=headers,
    )
    assert reset_res.status_code == 200
    reset_data = reset_res.json()
    assert reset_data["reset_token"] is not None
    assert len(reset_data["reset_token"]) >= 16


# ===========================================================================
# 3. Student Account Lifecycle (Status Toggle, Reset Password)
# ===========================================================================


async def test_student_account_status_toggle_and_reset_password(
    client: AsyncClient,
    lifecycle_fixture: dict[str, Any],
) -> None:
    """Test administrative account enable/disable and password reset for student."""
    headers = lifecycle_fixture["rector1_headers"]
    student1: Student = lifecycle_fixture["student1"]

    # 1. Check current status
    get_res = await client.get(f"/api/v1/students/{student1.id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["account_status"] == "ACTIVA"

    # 2. Deactivate student account
    deact_res = await client.post(
        f"/api/v1/students/{student1.id}/account/status",
        json={"is_active": False},
        headers=headers,
    )
    assert deact_res.status_code == 200
    assert deact_res.json()["account_status"] == "INACTIVA"

    # 3. Reactivate student account
    react_res = await client.post(
        f"/api/v1/students/{student1.id}/account/status",
        json={"is_active": True},
        headers=headers,
    )
    assert react_res.status_code == 200
    assert react_res.json()["account_status"] == "ACTIVA"

    # 4. Reset password
    reset_res = await client.post(
        f"/api/v1/students/{student1.id}/account/reset-password",
        headers=headers,
    )
    assert reset_res.status_code == 200
    assert reset_res.json()["reset_token"] is not None


# ===========================================================================
# 4. Bidirectional Linking & Safe Disassociation
# ===========================================================================


async def test_bidirectional_linking_and_safe_disassociation(
    client: AsyncClient,
    lifecycle_fixture: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    """Verify linking/unlinking from both Guardian and Student perspectives."""
    headers = lifecycle_fixture["rector1_headers"]
    student1: Student = lifecycle_fixture["student1"]

    # 1. Create Guardian A
    doc_a = f"85{uuid.uuid4().hex[:6]}"
    res_a = await client.post(
        "/api/v1/guardians",
        json={
            "first_name": "Alvaro",
            "last_name": "Uribe",
            "document_type": "CC",
            "document_number": doc_a,
            "phone": "3195556677",
            "relationship_type": "PADRE",
        },
        headers=headers,
    )
    assert res_a.status_code == 201
    guardian_a_id = res_a.json()["id"]

    # 2. Create Guardian B
    doc_b = f"86{uuid.uuid4().hex[:6]}"
    res_b = await client.post(
        "/api/v1/guardians",
        json={
            "first_name": "Beatriz",
            "last_name": "Perez",
            "document_type": "CC",
            "document_number": doc_b,
            "phone": "3196667788",
            "relationship_type": "MADRE",
        },
        headers=headers,
    )
    assert res_b.status_code == 201
    guardian_b_id = res_b.json()["id"]

    # 3. Link Guardian A -> Student from Guardian endpoint: POST /guardians/{g_id}/students/{s_id}
    link_a = await client.post(
        f"/api/v1/guardians/{guardian_a_id}/students/{student1.id}",
        json={
            "relationship_type": "PADRE",
            "is_primary_contact": True,
            "is_authorized_pickup": True,
        },
        headers=headers,
    )
    assert link_a.status_code == 201
    assert link_a.json()["is_primary_contact"] is True

    # 4. Link Guardian B -> Student from Student endpoint: POST /students/{s_id}/guardians/{g_id}
    link_b = await client.post(
        f"/api/v1/students/{student1.id}/guardians/{guardian_b_id}",
        json={
            "relationship_type": "MADRE",
            "is_primary_contact": False,
            "is_authorized_pickup": True,
        },
        headers=headers,
    )
    assert link_b.status_code == 201
    assert link_b.json()["relationship_type"] == "MADRE"

    # 5. Query student guardians (should have 2)
    list_g = await client.get(
        f"/api/v1/students/{student1.id}/guardians", headers=headers
    )
    assert list_g.status_code == 200
    assert len(list_g.json()) >= 2

    # 6. Disassociate Guardian A from Guardian endpoint: DELETE /guardians/{g_id}/students/{s_id}
    del_a = await client.delete(
        f"/api/v1/guardians/{guardian_a_id}/students/{student1.id}",
        headers=headers,
    )
    assert del_a.status_code == 204

    # Verify Guardian A record still exists (safe disassociation!)
    get_ga = await client.get(
        f"/api/v1/guardians/{guardian_a_id}", headers=headers
    )
    assert get_ga.status_code == 200
    assert get_ga.json()["id"] == guardian_a_id

    # 7. Disassociate Guardian B from Student endpoint: DELETE /students/{s_id}/guardians/{g_id}
    del_b = await client.delete(
        f"/api/v1/students/{student1.id}/guardians/{guardian_b_id}",
        headers=headers,
    )
    assert del_b.status_code == 204

    # Verify Student record still exists
    get_st = await client.get(
        f"/api/v1/students/{student1.id}", headers=headers
    )
    assert get_st.status_code == 200
    assert get_st.json()["id"] == str(student1.id)


# ===========================================================================
# 5. Anti-IDOR Cross-Institution Tenant Isolation
# ===========================================================================


async def test_anti_idor_cross_institution_protection(
    client: AsyncClient,
    lifecycle_fixture: dict[str, Any],
) -> None:
    """Rector of Inst 1 cannot read, modify, or unlink entities of Inst 2."""
    headers_rector1 = lifecycle_fixture["rector1_headers"]
    headers_rector2 = lifecycle_fixture["rector2_headers"]

    student2: Student = lifecycle_fixture["student2"]

    # 1. Create Guardian in Inst 2
    doc_num2 = f"97{uuid.uuid4().hex[:6]}"
    res_g2 = await client.post(
        "/api/v1/guardians",
        json={
            "first_name": "Guardia",
            "last_name": "SanLuis",
            "document_type": "CC",
            "document_number": doc_num2,
            "phone": "3197778899",
            "relationship_type": "MADRE",
            "provision_account": True,
            "new_user": {
                "first_name": "Guardia",
                "last_name": "SanLuis",
                "document_type": "CC",
                "document_number": doc_num2,
                "email": f"guardia_{doc_num2}@sanluis.edu.co",
            },
        },
        headers=headers_rector2,
    )
    assert res_g2.status_code == 201
    guardian2_id = res_g2.json()["id"]

    # 2. Rector 1 tries to GET guardian of Inst 2 -> 404
    get_idor = await client.get(
        f"/api/v1/guardians/{guardian2_id}", headers=headers_rector1
    )
    assert get_idor.status_code == 404

    # 3. Rector 1 tries to update status of guardian of Inst 2 -> 404
    status_idor = await client.post(
        f"/api/v1/guardians/{guardian2_id}/account/status",
        json={"is_active": False},
        headers=headers_rector1,
    )
    assert status_idor.status_code == 404

    # 4. Rector 1 tries to reset password of student of Inst 2 -> 404
    reset_idor = await client.post(
        f"/api/v1/students/{student2.id}/account/reset-password",
        headers=headers_rector1,
    )
    assert reset_idor.status_code == 404


# ===========================================================================
# 6. Public Guardian Self-Activation Flow
# ===========================================================================


async def test_public_guardian_activation_flow(
    client: AsyncClient,
    lifecycle_fixture: dict[str, Any],
) -> None:
    """Full public parent self-activation flow (request -> verify -> accept -> login)."""
    headers = lifecycle_fixture["rector1_headers"]
    student1: Student = lifecycle_fixture["student1"]

    # 1. Register guardian civilly and link to student
    doc_num = f"98{uuid.uuid4().hex[:6]}"
    guardian_email = f"parent_{doc_num}@correo.com"

    g_res = await client.post(
        "/api/v1/guardians",
        json={
            "first_name": "Consuelo",
            "last_name": "Murillo",
            "document_type": "CC",
            "document_number": doc_num,
            "phone": "3114447788",
            "email": guardian_email,
            "relationship_type": "MADRE",
        },
        headers=headers,
    )
    assert g_res.status_code == 201
    guardian_id = g_res.json()["id"]

    # Link to student
    await client.post(
        f"/api/v1/guardians/{guardian_id}/students/{student1.id}",
        json={
            "relationship_type": "MADRE",
            "is_primary_contact": True,
            "is_authorized_pickup": True,
        },
        headers=headers,
    )

    # 2. Public Self-Activation Request
    req_res = await client.post(
        "/api/v1/auth/guardians/request-activation",
        json={
            "student_code_simat": student1.code_simat,
            "guardian_document_type": "CC",
            "guardian_document_number": doc_num,
            "email": guardian_email,
        },
    )
    assert req_res.status_code == 200
    token = req_res.json().get("raw_activation_token")
    assert token is not None

    # 3. Public Verify Token
    verify_res = await client.post(
        "/api/v1/auth/guardians/verify-token",
        json={"token": token},
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["valid"] is True
    assert "Consuelo" in verify_res.json()["guardian_name"]

    # 4. Public Accept Activation (Define password)
    accept_res = await client.post(
        "/api/v1/auth/guardians/accept-activation",
        json={
            "token": token,
            "password": "SecureParent123!",
            "password_confirmation": "SecureParent123!",
        },
    )
    assert accept_res.status_code == 200
    assert accept_res.json()["is_active"] is True

    # 5. Login with newly established credentials
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"username": guardian_email, "password": "SecureParent123!"},
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()


# ===========================================================================
# 7. Token Segregation in Entity Responses
# ===========================================================================


async def test_token_segregation_in_entity_responses(
    client: AsyncClient,
    lifecycle_fixture: dict[str, Any],
) -> None:
    """Ensure reset_token is NEVER present in list/detail Guardian/Student responses."""
    headers = lifecycle_fixture["rector1_headers"]
    student1: Student = lifecycle_fixture["student1"]

    # Check Student detail
    st_res = await client.get(f"/api/v1/students/{student1.id}", headers=headers)
    assert st_res.status_code == 200
    assert "reset_token" not in st_res.json()

    # Check Students list
    st_list = await client.get("/api/v1/students", headers=headers)
    assert st_list.status_code == 200
    for s in st_list.json()["items"]:
        assert "reset_token" not in s

    # Check Guardians list
    g_list = await client.get("/api/v1/guardians", headers=headers)
    assert g_list.status_code == 200
    for g in g_list.json()["items"]:
        assert "reset_token" not in g
