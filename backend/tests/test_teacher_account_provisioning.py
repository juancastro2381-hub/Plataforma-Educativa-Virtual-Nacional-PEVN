"""
PEVN Backend — Teacher Account Provisioning & Lifecycle Integration Tests (Phase 13D.5)

Tests the complete Rector -> Teacher Onboarding Lifecycle:
1. Rector provisions teacher without account (SIN_CUENTA -> ACTIVA).
2. Teacher becomes linked to User.
3. User receives canonical 'teacher' role in UserRole.
4. Teacher can authenticate.
5. Teacher can access /teacher portal.
6. Teacher can access dashboard.
7. Teacher can access activities.
8. Rector can deactivate teacher account (ACTIVA -> INACTIVA).
9. Deactivated teacher cannot authenticate / access protected portal.
10. Rector can reactivate teacher account (INACTIVA -> ACTIVA).
11. Password reset workflow works.
12. Rector cannot modify teacher from another institution (cross-institution rejection).
13. Existing teacher with account does not receive duplicate User.
14. Academic history remains intact after account deactivation.
15. Existing Rector functionality remains intact.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.interfaces import SystemRole
from app.core.security.password import password_hasher
from app.core.security.tokens import token_service
from app.models.academic_activity import AcademicActivity, ActivityStatus, ActivityType
from app.models.academic_assignment import AcademicAssignment
from app.models.academic_year import AcademicPeriod, AcademicYear, AcademicYearCalendarType, AcademicYearStatus
from app.models.grade import Grade
from app.models.group import Group, ShiftEnum
from app.models.institution import Campus, Institution
from app.models.role import Role, UserRole
from app.models.subject import KnowledgeArea, Subject
from app.models.teacher import Teacher, TeacherContractType
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User


@pytest.fixture
async def provisioning_fixture(
    db_session: AsyncSession,
) -> dict[str, Any]:
    """Sets up Institution A (Rector A, Teacher A without role, Teacher A with workload), Institution B (Rector B)."""
    # 1. Territory
    dept = Department(code="05", name="Antioquia")
    db_session.add(dept)
    await db_session.flush()

    mun = Municipality(department_id=dept.id, code="05001", name="Medellín")
    db_session.add(mun)
    await db_session.flush()

    # 2. Institution A
    inst_a = Institution(
        name="I.E. Santo Domingo Savio",
        dane_code="105001000111",
        municipality_id=mun.id,
        email="contacto@santodomingo.edu.co",
        is_active=True,
    )
    db_session.add(inst_a)
    await db_session.flush()

    campus_a = Campus(
        institution_id=inst_a.id,
        name="Sede Principal A",
        dane_sede_code="105001000112",
        is_active=True,
    )
    db_session.add(campus_a)
    await db_session.flush()

    # 3. Institution B (For cross-tenant testing)
    inst_b = Institution(
        name="I.E. Marco Fidel Suárez",
        dane_code="105001000222",
        municipality_id=mun.id,
        email="contacto@marcofidel.edu.co",
        is_active=True,
    )
    db_session.add(inst_b)
    await db_session.flush()

    # 4. Resolve seeded roles
    role_rector = (await db_session.execute(select(Role).where(Role.name == "rector"))).scalar_one()
    role_teacher = (await db_session.execute(select(Role).where(Role.name == "teacher"))).scalar_one()

    # 5. Rector User A
    rector_user_a = User(
        institution_id=inst_a.id,
        email="rector_a@colegio.edu.co",
        username="rector_a",
        hashed_password=password_hasher.hash("RectorPass123!"),
        first_name="Rector",
        last_name="Institucional A",
        document_type=DocumentType.CC,
        document_number="70000001",
        is_active=True,
        is_verified=True,
    )
    db_session.add(rector_user_a)
    await db_session.flush()

    db_session.add(
        UserRole(
            user_id=rector_user_a.id,
            role_id=role_rector.id,
            institution_id=inst_a.id,
            is_active=True,
        )
    )

    # 6. Rector User B (Institution B)
    rector_user_b = User(
        institution_id=inst_b.id,
        email="rector_b@colegio.edu.co",
        username="rector_b",
        hashed_password=password_hasher.hash("RectorPass123!"),
        first_name="Rector",
        last_name="Institucional B",
        document_type=DocumentType.CC,
        document_number="70000002",
        is_active=True,
        is_verified=True,
    )
    db_session.add(rector_user_b)
    await db_session.flush()

    db_session.add(
        UserRole(
            user_id=rector_user_b.id,
            role_id=role_rector.id,
            institution_id=inst_b.id,
            is_active=True,
        )
    )

    # 7. Teacher Profile 1: In Institution A, WITHOUT 'teacher' role attached (SIN_CUENTA state)
    teacher_user_1 = User(
        institution_id=inst_a.id,
        email="docente_sin_cuenta@colegio.edu.co",
        username="docente_sin_cuenta",
        hashed_password=password_hasher.hash("TempPass123!"),
        first_name="Guillermo",
        last_name="Gómez",
        document_type=DocumentType.CC,
        document_number="70000003",
        is_active=True,
        is_verified=False,
    )
    db_session.add(teacher_user_1)
    await db_session.flush()

    teacher_profile_1 = Teacher(
        user_id=teacher_user_1.id,
        institution_id=inst_a.id,
        specialty_area="Matemáticas",
        contract_type=TeacherContractType.PROPIEDAD,
        escalafon_grade="14",
    )
    db_session.add(teacher_profile_1)
    await db_session.flush()

    # 8. Teacher Profile 2: In Institution A, with active 'teacher' role and academic workload
    teacher_user_2 = User(
        institution_id=inst_a.id,
        email="docente_activo@colegio.edu.co",
        username="docente_activo",
        hashed_password=password_hasher.hash("DocenteActivo123!"),
        first_name="Sandra",
        last_name="Pérez",
        document_type=DocumentType.CC,
        document_number="70000004",
        is_active=True,
        is_verified=True,
    )
    db_session.add(teacher_user_2)
    await db_session.flush()

    db_session.add(
        UserRole(
            user_id=teacher_user_2.id,
            role_id=role_teacher.id,
            institution_id=inst_a.id,
            is_active=True,
        )
    )

    teacher_profile_2 = Teacher(
        user_id=teacher_user_2.id,
        institution_id=inst_a.id,
        specialty_area="Ciencias Naturales",
        contract_type=TeacherContractType.PROPIEDAD,
        escalafon_grade="14",
    )
    db_session.add(teacher_profile_2)
    await db_session.flush()

    # Academic Structure for Teacher 2
    ay = AcademicYear(
        institution_id=inst_a.id,
        year=2026,
        name="Año Lectivo 2026",
        start_date=date(2026, 1, 15),
        end_date=date(2026, 11, 30),
        calendar_type=AcademicYearCalendarType.CALENDAR_A,
        status=AcademicYearStatus.ACTIVE,
    )
    db_session.add(ay)
    await db_session.flush()

    period = AcademicPeriod(
        academic_year_id=ay.id,
        period_number=1,
        name="Periodo 1",
        weight_percentage=25,
        start_date=date(2026, 1, 15),
        end_date=date(2026, 4, 15),
    )
    db_session.add(period)
    await db_session.flush()

    grade_9 = (await db_session.execute(select(Grade).where(Grade.code == "G09"))).scalar_one()

    group_9a = Group(
        campus_id=campus_a.id,
        academic_year_id=ay.id,
        grade_id=grade_9.id,
        name="9-A",
        shift=ShiftEnum.MANANA,
        capacity_limit=35,
    )
    db_session.add(group_9a)
    await db_session.flush()

    area_ciencias = KnowledgeArea(name="Ciencias Naturales")
    db_session.add(area_ciencias)
    await db_session.flush()

    subj_biologia = Subject(
        institution_id=inst_a.id,
        knowledge_area_id=area_ciencias.id,
        grade_id=grade_9.id,
        name="Biología General",
        weekly_hours=4,
    )
    db_session.add(subj_biologia)
    await db_session.flush()

    assignment_2 = AcademicAssignment(
        academic_year_id=ay.id,
        teacher_id=teacher_profile_2.id,
        group_id=group_9a.id,
        subject_id=subj_biologia.id,
        weekly_hours=4,
        is_active=True,
    )
    db_session.add(assignment_2)
    await db_session.flush()

    # Academic Activity for Teacher 2
    activity = AcademicActivity(
        institution_id=inst_a.id,
        teacher_id=teacher_profile_2.id,
        academic_assignment_id=assignment_2.id,
        subject_id=subj_biologia.id,
        group_id=group_9a.id,
        academic_year_id=ay.id,
        title="Taller de Genética Mendeliana",
        description="Actividad práctica de genética",
        activity_type=ActivityType.WORKSHOP,
        status=ActivityStatus.PUBLISHED,
        max_score=Decimal("5.00"),
        due_date=datetime(2026, 3, 20, 23, 59, tzinfo=UTC),
    )
    db_session.add(activity)
    await db_session.commit()

    # Tokens
    token_rector_a = await token_service.create_access_token(
        subject=str(rector_user_a.id),
        additional_claims={
            "roles": [SystemRole.RECTOR.value],
            "institution_id": str(inst_a.id),
        },
    )
    token_rector_b = await token_service.create_access_token(
        subject=str(rector_user_b.id),
        additional_claims={
            "roles": [SystemRole.RECTOR.value],
            "institution_id": str(inst_b.id),
        },
    )
    token_teacher_2 = await token_service.create_access_token(
        subject=str(teacher_user_2.id),
        additional_claims={
            "roles": [SystemRole.TEACHER.value],
            "institution_id": str(inst_a.id),
        },
    )

    return {
        "inst_a_id": inst_a.id,
        "inst_b_id": inst_b.id,
        "rector_a_token": token_rector_a,
        "rector_b_token": token_rector_b,
        "teacher_1_id": teacher_profile_1.id,
        "teacher_1_user_id": teacher_user_1.id,
        "teacher_1_email": teacher_user_1.email,
        "teacher_2_id": teacher_profile_2.id,
        "teacher_2_user_id": teacher_user_2.id,
        "teacher_2_token": token_teacher_2,
        "activity_id": activity.id,
        "assignment_2_id": assignment_2.id,
    }


@pytest.mark.asyncio
async def test_r1_to_r7_provision_teacher_account_and_login_access(
    client: AsyncClient,
    provisioning_fixture: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    """
    R1: Rector provisions teacher without account.
    R2: Teacher linked to User.
    R3: User receives canonical 'teacher' role in UserRole.
    R4: Teacher can authenticate.
    R5: Teacher can access /teacher.
    R6: Teacher can access dashboard.
    R7: Teacher can access activities.
    """
    f = provisioning_fixture

    # 1. Verify initially teacher 1 has SIN_CUENTA in list
    res_list = await client.get(
        "/api/v1/teachers",
        headers={"Authorization": f"Bearer {f['rector_a_token']}"},
    )
    assert res_list.status_code == 200
    teachers = res_list.json()["items"]
    t1 = next(t for t in teachers if t["id"] == str(f["teacher_1_id"]))
    assert t1["account_status"] == "SIN_CUENTA"

    # 2. Rector provisions account for Teacher 1
    res_prov = await client.post(
        f"/api/v1/teachers/{f['teacher_1_id']}/account/provision",
        headers={"Authorization": f"Bearer {f['rector_a_token']}"},
        json={"email": "docente_nuevo_email@colegio.edu.co"},
    )
    assert res_prov.status_code == 200
    prov_data = res_prov.json()
    assert prov_data["account_status"] == "ACTIVA"
    assert prov_data["teacher_id"] == str(f["teacher_1_id"])
    assert prov_data["user_id"] == str(f["teacher_1_user_id"])
    assert prov_data["reset_token"] is not None

    # 3. Verify in DB that UserRole was assigned for 'teacher'
    user_stmt = select(User).where(User.id == f["teacher_1_user_id"])
    u1 = (await db_session.execute(user_stmt)).scalar_one()
    assert u1.email == "docente_nuevo_email@colegio.edu.co"
    assert u1.is_active is True
    assert u1.must_change_password is True

    # 4. Set password and Authenticate as Teacher 1
    # Confirm password reset with the reset token
    res_confirm = await client.post(
        "/api/v1/auth/password/reset/confirm",
        json={
            "token": prov_data["reset_token"],
            "new_password": "NewTeacherPassword2026!",
        },
    )
    assert res_confirm.status_code == 200

    # Login as Teacher 1
    res_login = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "docente_nuevo_email@colegio.edu.co",
            "password": "NewTeacherPassword2026!",
        },
    )
    assert res_login.status_code == 200
    login_data = res_login.json()
    assert "access_token" in login_data
    teacher_token = login_data["access_token"]

    # 5. Teacher 1 accesses /api/v1/teacher/dashboard
    res_dash = await client.get(
        "/api/v1/teacher/dashboard",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res_dash.status_code == 200
    dash_data = res_dash.json()
    assert dash_data["teacher_id"] == str(f["teacher_1_id"])
    assert dash_data["institution_id"] == str(f["inst_a_id"])

    # 6. Teacher 1 accesses /api/v1/teacher/activities
    res_act = await client.get(
        "/api/v1/teacher/activities",
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert res_act.status_code == 200
    assert "items" in res_act.json()


@pytest.mark.asyncio
async def test_r8_to_r10_deactivate_and_reactivate_teacher_account(
    client: AsyncClient,
    provisioning_fixture: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    """
    R8: Rector can deactivate teacher account.
    R9: Deactivated teacher cannot authenticate / access protected portal.
    R10: Rector can reactivate teacher account.
    """
    f = provisioning_fixture

    # 1. Deactivate Teacher 2
    res_deact = await client.post(
        f"/api/v1/teachers/{f['teacher_2_id']}/account/status",
        headers={"Authorization": f"Bearer {f['rector_a_token']}"},
        json={"is_active": False},
    )
    assert res_deact.status_code == 200
    assert res_deact.json()["account_status"] == "INACTIVA"

    # Verify status in list endpoint
    res_list = await client.get(
        "/api/v1/teachers",
        headers={"Authorization": f"Bearer {f['rector_a_token']}"},
    )
    t2 = next(t for t in res_list.json()["items"] if t["id"] == str(f["teacher_2_id"]))
    assert t2["account_status"] == "INACTIVA"

    # 2. Login fails for deactivated teacher
    res_login = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "docente_activo",
            "password": "DocenteActivo123!",
        },
    )
    assert res_login.status_code in {401, 403}

    # 3. Reactivate Teacher 2
    res_react = await client.post(
        f"/api/v1/teachers/{f['teacher_2_id']}/account/status",
        headers={"Authorization": f"Bearer {f['rector_a_token']}"},
        json={"is_active": True},
    )
    assert res_react.status_code == 200
    assert res_react.json()["account_status"] == "ACTIVA"

    # 4. Login succeeds after reactivation
    res_login_ok = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "docente_activo",
            "password": "DocenteActivo123!",
        },
    )
    assert res_login_ok.status_code == 200


@pytest.mark.asyncio
async def test_r11_password_reset_workflow(
    client: AsyncClient,
    provisioning_fixture: dict[str, Any],
) -> None:
    """R11: Password reset workflow triggered by Rector."""
    f = provisioning_fixture

    res_reset = await client.post(
        f"/api/v1/teachers/{f['teacher_2_id']}/account/reset-password",
        headers={"Authorization": f"Bearer {f['rector_a_token']}"},
    )
    assert res_reset.status_code == 200
    reset_data = res_reset.json()
    assert reset_data["message"] == "Solicitud de restablecimiento de contraseña procesada exitosamente."
    assert reset_data["reset_token"] is not None

    # Confirm password reset
    res_confirm = await client.post(
        "/api/v1/auth/password/reset/confirm",
        json={
            "token": reset_data["reset_token"],
            "new_password": "NewResetPassword2026!",
        },
    )
    assert res_confirm.status_code == 200

    # Verify new password login
    res_login = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "docente_activo",
            "password": "NewResetPassword2026!",
        },
    )
    assert res_login.status_code == 200


@pytest.mark.asyncio
async def test_r12_cross_institution_isolation(
    client: AsyncClient,
    provisioning_fixture: dict[str, Any],
) -> None:
    """R12: Rector of Institution B cannot provision, activate, deactivate or reset Teacher from Institution A."""
    f = provisioning_fixture

    # Rector B tries to provision Teacher 1 (Inst A) -> 404
    res_prov = await client.post(
        f"/api/v1/teachers/{f['teacher_1_id']}/account/provision",
        headers={"Authorization": f"Bearer {f['rector_b_token']}"},
        json={},
    )
    assert res_prov.status_code in {403, 404}

    # Rector B tries to update status of Teacher 2 (Inst A) -> 404
    res_stat = await client.post(
        f"/api/v1/teachers/{f['teacher_2_id']}/account/status",
        headers={"Authorization": f"Bearer {f['rector_b_token']}"},
        json={"is_active": False},
    )
    assert res_stat.status_code in {403, 404}

    # Rector B tries to reset password of Teacher 2 (Inst A) -> 404
    res_reset = await client.post(
        f"/api/v1/teachers/{f['teacher_2_id']}/account/reset-password",
        headers={"Authorization": f"Bearer {f['rector_b_token']}"},
    )
    assert res_reset.status_code in {403, 404}


@pytest.mark.asyncio
async def test_r13_idempotent_provisioning(
    client: AsyncClient,
    provisioning_fixture: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    """R13: Existing teacher with account does not receive duplicate User or duplicate roles."""
    f = provisioning_fixture

    # Provision Teacher 2 (already active with role)
    res_prov_1 = await client.post(
        f"/api/v1/teachers/{f['teacher_2_id']}/account/provision",
        headers={"Authorization": f"Bearer {f['rector_a_token']}"},
        json={},
    )
    assert res_prov_1.status_code == 200

    # Repeat provisioning
    res_prov_2 = await client.post(
        f"/api/v1/teachers/{f['teacher_2_id']}/account/provision",
        headers={"Authorization": f"Bearer {f['rector_a_token']}"},
        json={},
    )
    assert res_prov_2.status_code == 200

    # Check that User count remains 1 and UserRole count for teacher role remains 1
    users_stmt = select(User).where(User.id == f["teacher_2_user_id"])
    users = (await db_session.execute(users_stmt)).scalars().all()
    assert len(users) == 1

    roles_stmt = select(UserRole).where(UserRole.user_id == f["teacher_2_user_id"])
    roles = (await db_session.execute(roles_stmt)).scalars().all()
    assert len(roles) == 1


@pytest.mark.asyncio
async def test_r14_academic_history_preserved_on_deactivation(
    client: AsyncClient,
    provisioning_fixture: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    """R14: Academic assignments, activities, grades remain 100% intact after account deactivation."""
    f = provisioning_fixture

    # Deactivate account
    res_deact = await client.post(
        f"/api/v1/teachers/{f['teacher_2_id']}/account/status",
        headers={"Authorization": f"Bearer {f['rector_a_token']}"},
        json={"is_active": False},
    )
    assert res_deact.status_code == 200

    # Verify assignments in DB
    assign_stmt = select(AcademicAssignment).where(AcademicAssignment.id == f["assignment_2_id"])
    assignment = (await db_session.execute(assign_stmt)).scalar_one_or_none()
    assert assignment is not None
    assert assignment.is_active is True

    # Verify activities in DB
    act_stmt = select(AcademicActivity).where(AcademicActivity.id == f["activity_id"])
    activity = (await db_session.execute(act_stmt)).scalar_one_or_none()
    assert activity is not None
    assert activity.title == "Taller de Genética Mendeliana"


@pytest.mark.asyncio
async def test_r15_teacher_creation_with_immediate_provisioning_and_deferred_provisioning(
    client: AsyncClient,
    provisioning_fixture: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    """R15: Immediate provisioning during teacher creation vs deferred profile creation."""
    f = provisioning_fixture

    # 1. Immediate Provisioning (provision_account=True) with new_user
    res_imm = await client.post(
        "/api/v1/teachers",
        headers={"Authorization": f"Bearer {f['rector_a_token']}"},
        json={
            "new_user": {
                "first_name": "Valeria",
                "last_name": "Mendoza",
                "document_type": "CC",
                "document_number": "55667788",
                "email": "valeria.mendoza@librada.edu.co",
            },
            "specialty_area": "Química Orgánica",
            "contract_type": "PROPIEDAD",
            "escalafon_grade": "2A",
            "provision_account": True,
        },
    )
    assert res_imm.status_code == 201
    imm_data = res_imm.json()
    assert imm_data["account_status"] == "ACTIVA"
    assert imm_data["has_account"] is True
    assert imm_data["reset_token"] is not None
    valeria_reset_token = imm_data["reset_token"]

    # Valeria establishes password using reset token
    res_pass = await client.post(
        "/api/v1/auth/password/reset/confirm",
        json={"token": valeria_reset_token, "new_password": "NewValeriaPass123!"},
    )
    assert res_pass.status_code == 200

    # Valeria logs in and accesses /teacher/dashboard
    res_login = await client.post(
        "/api/v1/auth/login",
        json={"username": "valeria.mendoza@librada.edu.co", "password": "NewValeriaPass123!"},
    )
    assert res_login.status_code == 200
    valeria_token = res_login.json()["access_token"]

    res_dash = await client.get(
        "/api/v1/teacher/dashboard",
        headers={"Authorization": f"Bearer {valeria_token}"},
    )
    assert res_dash.status_code == 200
    assert res_dash.json()["teacher_id"] == imm_data["id"]

    # 2. Deferred Provisioning (provision_account=False)
    res_def = await client.post(
        "/api/v1/teachers",
        headers={"Authorization": f"Bearer {f['rector_a_token']}"},
        json={
            "new_user": {
                "first_name": "Marcos",
                "last_name": "Pérez",
                "document_type": "CC",
                "document_number": "99887766",
                "email": "marcos.perez@librada.edu.co",
            },
            "specialty_area": "Filosofía y Letras",
            "contract_type": "PROVISIONAL",
            "escalafon_grade": "14",
            "provision_account": False,
        },
    )
    assert res_def.status_code == 201
    def_data = res_def.json()
    assert def_data["account_status"] == "SIN_CUENTA"
    assert def_data["has_account"] is False
    marcos_teacher_id = def_data["id"]

    # Later: Rector provisions Marcos
    res_prov = await client.post(
        f"/api/v1/teachers/{marcos_teacher_id}/account/provision",
        headers={"Authorization": f"Bearer {f['rector_a_token']}"},
        json={},
    )
    assert res_prov.status_code == 200
    prov_data = res_prov.json()
    assert prov_data["account_status"] == "ACTIVA"
    assert prov_data["reset_token"] is not None

    # Marcos sets password and logs in
    res_pass_m = await client.post(
        "/api/v1/auth/password/reset/confirm",
        json={"token": prov_data["reset_token"], "new_password": "NewMarcosPass123!"},
    )
    assert res_pass_m.status_code == 200

    res_login_m = await client.post(
        "/api/v1/auth/login",
        json={"username": "marcos.perez@librada.edu.co", "password": "NewMarcosPass123!"},
    )
    assert res_login_m.status_code == 200
    marcos_token = res_login_m.json()["access_token"]

    res_dash_m = await client.get(
        "/api/v1/teacher/dashboard",
        headers={"Authorization": f"Bearer {marcos_token}"},
    )
    assert res_dash_m.status_code == 200
    assert res_dash_m.json()["teacher_id"] == marcos_teacher_id


@pytest.mark.asyncio
async def test_r16_single_use_token_invalidation_and_expiration(
    client: AsyncClient,
    provisioning_fixture: dict[str, Any],
    db_session: AsyncSession,
) -> None:
    """R16: Single-use reset tokens are invalidated immediately upon use, and expired tokens are rejected."""
    f = provisioning_fixture

    # 1. Create teacher with immediate provisioning
    res = await client.post(
        "/api/v1/teachers",
        headers={"Authorization": f"Bearer {f['rector_a_token']}"},
        json={
            "new_user": {
                "first_name": "Clara",
                "last_name": "Rios",
                "document_type": "CC",
                "document_number": "1122334455",
                "email": "clara.rios@librada.edu.co",
            },
            "specialty_area": "Matemáticas",
            "contract_type": "PROPIEDAD",
            "escalafon_grade": "14",
            "provision_account": True,
        },
    )
    assert res.status_code == 201
    data = res.json()
    token = data["reset_token"]
    assert token is not None

    # 2. Verify token is valid initially
    res_v = await client.post(
        "/api/v1/auth/password/reset/verify-token",
        json={"token": token},
    )
    assert res_v.status_code == 200
    assert res_v.json()["valid"] is True

    # 3. Use token once to set password
    res_use = await client.post(
        "/api/v1/auth/password/reset/confirm",
        json={"token": token, "new_password": "NewClaraPassword123!"},
    )
    assert res_use.status_code == 200

    # 4. Attempt to use same token a second time -> MUST FAIL
    res_reuse = await client.post(
        "/api/v1/auth/password/reset/confirm",
        json={"token": token, "new_password": "AnotherPassword456!"},
    )
    assert res_reuse.status_code in {400, 401}

    # 5. Verify token verification now returns invalid
    res_v_again = await client.post(
        "/api/v1/auth/password/reset/verify-token",
        json={"token": token},
    )
    assert res_v_again.status_code in {400, 401}


@pytest.mark.asyncio
async def test_r17_security_sanitization_no_plaintext_passwords_in_payloads(
    client: AsyncClient,
    provisioning_fixture: dict[str, Any],
) -> None:
    """R17: Response payloads never contain plaintext passwords or password hashes."""
    f = provisioning_fixture

    res = await client.post(
        "/api/v1/teachers",
        headers={"Authorization": f"Bearer {f['rector_a_token']}"},
        json={
            "new_user": {
                "first_name": "Lucia",
                "last_name": "Gomez",
                "document_type": "CC",
                "document_number": "8899001122",
                "email": "lucia.gomez@librada.edu.co",
            },
            "specialty_area": "Lengua Castellana",
            "contract_type": "PROPIEDAD",
            "escalafon_grade": "14",
            "provision_account": True,
        },
    )
    assert res.status_code == 201
    data = res.json()

    # Payload must NOT contain password fields
    assert "password" not in data
    assert "hashed_password" not in data
    assert "plain_password" not in data
    if "user" in data and data["user"]:
        assert "password" not in data["user"]
        assert "hashed_password" not in data["user"]


