"""
PEVN Backend - SIEE Evaluation, Report Card & Promotion REST API Tests (Phase 16C)

Automated end-to-end integration and security test suite for:
1. SIEE Policies API (Active resolution, versioning, audit trail)
2. Evaluation Period Consolidation Sheet & Grades Saving (with mandatory adjustment_reason)
3. Recovery Grade Recording & Capping
4. Academic Period Closure and Reopening Workflows
5. Student & Group Report Cards with strict Anti-IDOR enforcement
6. Academic Promotion Preview & Commit (PROMOVIDO vs GRADUADO semantics)
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
from app.models.academic_assignment import AcademicAssignment
from app.models.academic_year import (
    AcademicPeriod,
    AcademicYear,
    AcademicYearCalendarType,
    AcademicYearStatus,
)
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.evaluation import (
    PerformanceLevelEnum,
    PeriodSubjectGrade,
    PromotionStatusEnum,
    SieePolicy,
)
from app.models.grade import EducationalLevel, Grade
from app.models.group import Group, ShiftEnum
from app.models.guardian import Guardian, GuardianRelationshipType, StudentGuardian
from app.models.institution import Campus, Institution
from app.models.role import Role, UserRole
from app.models.student import Student, StudentGender
from app.models.subject import KnowledgeArea, Subject
from app.models.teacher import Teacher, TeacherContractType
from app.models.territory import Department, Municipality
from app.models.user import DocumentType, User
from app.services.rbac_bootstrap_service import RbacBootstrapService


@pytest.fixture
async def siee_api_fixture(db_session: AsyncSession) -> dict[str, Any]:
    """Sets up institution, groups, assigned/unassigned teachers, students, guardian, and tokens."""
    # Ensure canonical RBAC is fully bootstrapped in test DB
    rbac_svc = RbacBootstrapService(db_session)
    await rbac_svc.seed_canonical_rbac_if_needed()
    await db_session.flush()

    dept = Department(code="11", name="Bogota D.C.")
    db_session.add(dept)
    await db_session.flush()

    mun = Municipality(department_id=dept.id, code="11001", name="Bogota D.C.")
    db_session.add(mun)
    await db_session.flush()

    inst = Institution(
        dane_code="111111111111",
        name="Instituto Nacional de Prueba SIEE",
        email="rector.siee@pevn.edu.co",
        municipality_id=mun.id,
        is_active=True,
    )
    db_session.add(inst)
    await db_session.flush()

    campus = Campus(
        institution_id=inst.id,
        dane_sede_code="11111111111101",
        name="Sede Principal SIEE",
        is_active=True,
    )
    db_session.add(campus)
    await db_session.flush()

    res9 = await db_session.execute(select(Grade).where(Grade.code == "G09"))
    grade_9 = res9.scalar_one_or_none()
    if not grade_9:
        grade_9 = Grade(code="G09", name="Grado Noveno", level=EducationalLevel.SECUNDARIA, ordinal_order=9)
        db_session.add(grade_9)
        await db_session.flush()

    res11 = await db_session.execute(select(Grade).where(Grade.code == "G11"))
    grade_11 = res11.scalar_one_or_none()
    if not grade_11:
        grade_11 = Grade(code="G11", name="Grado Once", level=EducationalLevel.MEDIA, ordinal_order=11)
        db_session.add(grade_11)
        await db_session.flush()

    year_2026 = AcademicYear(
        institution_id=inst.id,
        name="Ano 2026",
        year=2026,
        status=AcademicYearStatus.ACTIVE,
        calendar_type=AcademicYearCalendarType.CALENDAR_A,
        start_date=datetime(2026, 1, 20).date(),
        end_date=datetime(2026, 11, 30).date(),
    )
    db_session.add(year_2026)
    await db_session.flush()

    period_1 = AcademicPeriod(
        academic_year_id=year_2026.id,
        period_number=1,
        name="Primer Periodo",
        weight_percentage=Decimal("25.00"),
        start_date=datetime(2026, 1, 20).date(),
        end_date=datetime(2026, 4, 15).date(),
        is_closed=False,
    )
    db_session.add(period_1)
    await db_session.flush()

    group_9a = Group(
        academic_year_id=year_2026.id,
        campus_id=campus.id,
        grade_id=grade_9.id,
        name="9-A",
        shift=ShiftEnum.MANANA,
    )
    group_11a = Group(
        academic_year_id=year_2026.id,
        campus_id=campus.id,
        grade_id=grade_11.id,
        name="11-A",
        shift=ShiftEnum.MANANA,
    )
    db_session.add_all([group_9a, group_11a])
    await db_session.flush()

    area = KnowledgeArea(institution_id=inst.id, name="Matematicas", is_mandatory=True)
    db_session.add(area)
    await db_session.flush()

    subject_mat = Subject(
        institution_id=inst.id,
        knowledge_area_id=area.id,
        grade_id=grade_9.id,
        name="Algebra",
        weekly_hours=4,
    )
    db_session.add(subject_mat)
    await db_session.flush()

    # Roles map
    roles_res = await db_session.execute(select(Role))
    roles_map = {r.name: r for r in roles_res.scalars().all()}

    # Users
    rector_user = User(
        email="rector.siee@pevn.edu.co",
        username="rector_siee",
        hashed_password=password_hasher.hash("RectorPass123!"),
        document_type=DocumentType.CC,
        document_number="80001",
        first_name="Guillermo",
        last_name="Rector",
        institution_id=inst.id,
        is_active=True,
    )
    teacher_assigned_user = User(
        email="docente.assigned.siee@pevn.edu.co",
        username="docente_assigned_siee",
        hashed_password=password_hasher.hash("TeacherPass123!"),
        document_type=DocumentType.CC,
        document_number="80002",
        first_name="Carlos",
        last_name="Profesor",
        institution_id=inst.id,
        is_active=True,
    )
    teacher_unassigned_user = User(
        email="docente.unassigned.siee@pevn.edu.co",
        username="docente_unassigned_siee",
        hashed_password=password_hasher.hash("TeacherPass123!"),
        document_type=DocumentType.CC,
        document_number="80003",
        first_name="Luis",
        last_name="NoAsignado",
        institution_id=inst.id,
        is_active=True,
    )
    student1_user = User(
        email="estudiante.uno.siee@pevn.edu.co",
        username="estudiante1_siee",
        hashed_password=password_hasher.hash("StudentPass123!"),
        document_type=DocumentType.TI,
        document_number="80004",
        first_name="Juan",
        last_name="Estudiante",
        institution_id=inst.id,
        is_active=True,
    )
    student2_user = User(
        email="estudiante.dos.siee@pevn.edu.co",
        username="estudiante2_siee",
        hashed_password=password_hasher.hash("StudentPass123!"),
        document_type=DocumentType.TI,
        document_number="80005",
        first_name="Pedro",
        last_name="Estudiante",
        institution_id=inst.id,
        is_active=True,
    )
    guardian_user = User(
        email="acudiente.siee@pevn.edu.co",
        username="acudiente_siee",
        hashed_password=password_hasher.hash("GuardianPass123!"),
        document_type=DocumentType.CC,
        document_number="80006",
        first_name="Maria",
        last_name="Acudiente",
        institution_id=inst.id,
        is_active=True,
    )
    db_session.add_all([
        rector_user,
        teacher_assigned_user,
        teacher_unassigned_user,
        student1_user,
        student2_user,
        guardian_user,
    ])
    await db_session.flush()

    db_session.add(UserRole(user_id=rector_user.id, role_id=roles_map["rector"].id))
    db_session.add(UserRole(user_id=teacher_assigned_user.id, role_id=roles_map["teacher"].id))
    db_session.add(UserRole(user_id=teacher_unassigned_user.id, role_id=roles_map["teacher"].id))
    db_session.add(UserRole(user_id=student1_user.id, role_id=roles_map["student"].id))
    db_session.add(UserRole(user_id=student2_user.id, role_id=roles_map["student"].id))
    db_session.add(UserRole(user_id=guardian_user.id, role_id=roles_map["guardian"].id))
    await db_session.flush()

    # Teacher entities
    teacher_assigned = Teacher(
        user_id=teacher_assigned_user.id,
        institution_id=inst.id,
        specialty_area="Matematicas",
        contract_type=TeacherContractType.PROPIEDAD,
    )
    teacher_unassigned = Teacher(
        user_id=teacher_unassigned_user.id,
        institution_id=inst.id,
        specialty_area="Ciencias",
        contract_type=TeacherContractType.PROPIEDAD,
    )
    db_session.add_all([teacher_assigned, teacher_unassigned])
    await db_session.flush()

    # Academic assignment for assigned teacher in 9-A Math
    assignment = AcademicAssignment(
        academic_year_id=year_2026.id,
        group_id=group_9a.id,
        subject_id=subject_mat.id,
        teacher_id=teacher_assigned.id,
        weekly_hours=4,
        is_active=True,
    )
    db_session.add(assignment)
    await db_session.flush()

    # Student entities & enrollments
    student1 = Student(
        user_id=student1_user.id,
        institution_id=inst.id,
        code_simat="SIMAT-80001",
        birth_date=datetime(2010, 5, 10).date(),
        gender=StudentGender.M,
    )
    student2 = Student(
        user_id=student2_user.id,
        institution_id=inst.id,
        code_simat="SIMAT-80002",
        birth_date=datetime(2010, 6, 12).date(),
        gender=StudentGender.M,
    )
    db_session.add_all([student1, student2])
    await db_session.flush()

    enr1 = Enrollment(
        student_id=student1.id,
        academic_year_id=year_2026.id,
        group_id=group_9a.id,
        status=EnrollmentStatus.ACTIVE,
    )
    enr2 = Enrollment(
        student_id=student2.id,
        academic_year_id=year_2026.id,
        group_id=group_9a.id,
        status=EnrollmentStatus.ACTIVE,
    )
    db_session.add_all([enr1, enr2])
    await db_session.flush()

    # Guardian entity linked ONLY to student1
    guardian = Guardian(
        user_id=guardian_user.id,
        institution_id=inst.id,
        document_type=DocumentType.CC,
        document_number="80006",
        first_name="Maria",
        last_name="Acudiente",
        phone="3001234567",
        relationship_type=GuardianRelationshipType.MADRE,
    )
    db_session.add(guardian)
    await db_session.flush()

    link1 = StudentGuardian(
        guardian_id=guardian.id,
        student_id=student1.id,
        relationship_type=GuardianRelationshipType.MADRE,
        is_primary_contact=True,
        is_authorized_pickup=True,
    )
    db_session.add(link1)
    await db_session.flush()

    # JWT Tokens
    rector_token = await token_service.create_access_token(
        subject=str(rector_user.id),
        additional_claims={"email": rector_user.email, "roles": ["rector"]},
    )
    teacher_assigned_token = await token_service.create_access_token(
        subject=str(teacher_assigned_user.id),
        additional_claims={"email": teacher_assigned_user.email, "roles": ["teacher"]},
    )
    teacher_unassigned_token = await token_service.create_access_token(
        subject=str(teacher_unassigned_user.id),
        additional_claims={"email": teacher_unassigned_user.email, "roles": ["teacher"]},
    )
    student1_token = await token_service.create_access_token(
        subject=str(student1_user.id),
        additional_claims={"email": student1_user.email, "roles": ["student"]},
    )
    student2_token = await token_service.create_access_token(
        subject=str(student2_user.id),
        additional_claims={"email": student2_user.email, "roles": ["student"]},
    )
    guardian_token = await token_service.create_access_token(
        subject=str(guardian_user.id),
        additional_claims={"email": guardian_user.email, "roles": ["guardian"]},
    )

    return {
        "institution": inst,
        "academic_year": year_2026,
        "period": period_1,
        "group_9a": group_9a,
        "group_11a": group_11a,
        "subject_mat": subject_mat,
        "student1": student1,
        "student2": student2,
        "enr1": enr1,
        "enr2": enr2,
        "rector_token": rector_token,
        "teacher_assigned_token": teacher_assigned_token,
        "teacher_unassigned_token": teacher_unassigned_token,
        "student1_token": student1_token,
        "student2_token": student2_token,
        "guardian_token": guardian_token,
    }


# ===========================================================================
# 1. SIEE Policies API Tests
# ===========================================================================


@pytest.mark.asyncio
async def test_siee_policies_api_active_and_versioning(
    client: AsyncClient,
    siee_api_fixture: dict[str, Any],
) -> None:
    f = siee_api_fixture
    year_id = str(f["academic_year"].id)

    # 1. Active policy resolution (bootstraps standard)
    resp = await client.get(
        f"/api/v1/siee-policies/active?academic_year_id={year_id}",
        headers={"Authorization": f"Bearer {f['rector_token']}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["version"] == 1
    assert data["min_passing_score"] == 3.00
    assert data["is_active"] is True

    # 2. Publish new version
    create_payload = {
        "name": "SIEE 2026 v2 - Ajuste de Escala",
        "description": "Aprobado en Consejo Directivo Acta 04",
        "min_passing_score": 3.20,
        "max_score": 5.00,
        "low_threshold_max": 3.19,
        "basic_threshold_max": 3.99,
        "high_threshold_max": 4.59,
        "recovery_grade_cap": 3.20,
        "max_failed_subjects_for_promotion": 2,
        "max_failed_core_subjects": 1,
        "min_attendance_percentage": 80.0,
        "attendance_affects_promotion": True,
        "rounding_decimals": 1,
        "is_active": True,
    }
    create_resp = await client.post(
        f"/api/v1/siee-policies?academic_year_id={year_id}",
        headers={"Authorization": f"Bearer {f['rector_token']}"},
        json=create_payload,
    )
    assert create_resp.status_code == 201, create_resp.text
    new_data = create_resp.json()
    assert new_data["version"] == 2
    assert new_data["min_passing_score"] == 3.20
    assert new_data["is_active"] is True

    # 3. Policy History
    hist_resp = await client.get(
        f"/api/v1/siee-policies/history?academic_year_id={year_id}",
        headers={"Authorization": f"Bearer {f['rector_token']}"},
    )
    assert hist_resp.status_code == 200, hist_resp.text
    hist_data = hist_resp.json()
    assert hist_data["total"] == 2
    assert hist_data["items"][0]["version"] == 2
    assert hist_data["items"][0]["is_active"] is True
    assert hist_data["items"][1]["version"] == 1
    assert hist_data["items"][1]["is_active"] is False

    # 4. Teacher unauthorized to manage SIEE policy
    teacher_create_resp = await client.post(
        f"/api/v1/siee-policies?academic_year_id={year_id}",
        headers={"Authorization": f"Bearer {f['teacher_assigned_token']}"},
        json=create_payload,
    )
    assert teacher_create_resp.status_code == 403


# ===========================================================================
# 2. Evaluation Period Consolidation & Adjustment Reason Invariant Tests
# ===========================================================================


@pytest.mark.asyncio
async def test_period_sheet_and_save_period_grades_with_reason(
    client: AsyncClient,
    siee_api_fixture: dict[str, Any],
) -> None:
    f = siee_api_fixture
    p_id = str(f["period"].id)
    g_id = str(f["group_9a"].id)
    s_id = str(f["subject_mat"].id)
    st1_id = str(f["student1"].id)
    enr1_id = str(f["enr1"].id)
    st2_id = str(f["student2"].id)
    enr2_id = str(f["enr2"].id)

    # 1. Fetch period sheet
    sheet_resp = await client.get(
        f"/api/v1/evaluations/period-sheet?period_id={p_id}&group_id={g_id}&subject_id={s_id}",
        headers={"Authorization": f"Bearer {f['teacher_assigned_token']}"},
    )
    assert sheet_resp.status_code == 200, sheet_resp.text
    sheet_data = sheet_resp.json()
    assert len(sheet_data["students"]) == 2

    # 2. Unassigned teacher cannot access sheet
    unassigned_resp = await client.get(
        f"/api/v1/evaluations/period-sheet?period_id={p_id}&group_id={g_id}&subject_id={s_id}",
        headers={"Authorization": f"Bearer {f['teacher_unassigned_token']}"},
    )
    assert unassigned_resp.status_code == 403

    # 3. Save grades with final_score != calculated_score WITHOUT reason -> 400 Bad Request
    invalid_save_payload = {
        "period_id": p_id,
        "group_id": g_id,
        "subject_id": s_id,
        "items": [
            {
                "student_id": st1_id,
                "enrollment_id": enr1_id,
                "calculated_score": 2.8,
                "final_score": 3.5,
                "adjustment_reason": None,  # Missing mandatory justification
                "total_absences": 1,
                "unexcused_absences": 0,
            }
        ],
    }
    save_fail_resp = await client.post(
        "/api/v1/evaluations/period-grades",
        headers={"Authorization": f"Bearer {f['teacher_assigned_token']}"},
        json=invalid_save_payload,
    )
    assert save_fail_resp.status_code == 400, save_fail_resp.text
    assert "justificación" in save_fail_resp.text.lower() or "justificacion" in save_fail_resp.text.lower() or "ADJUSTMENT_REASON_REQUIRED" in save_fail_resp.text

    # 4. Save grades with mandatory justification -> 200 OK
    valid_save_payload = {
        "period_id": p_id,
        "group_id": g_id,
        "subject_id": s_id,
        "items": [
            {
                "student_id": st1_id,
                "enrollment_id": enr1_id,
                "calculated_score": 2.8,
                "final_score": 3.5,
                "adjustment_reason": "Participacion destacada en olimpiadas de algebra",
                "observations": "Demuestra gran avance",
                "total_absences": 1,
                "unexcused_absences": 0,
            },
            {
                "student_id": st2_id,
                "enrollment_id": enr2_id,
                "calculated_score": 2.5,
                "final_score": 2.5,
                "adjustment_reason": None,
                "observations": "Requiere plan de mejoramiento",
                "total_absences": 3,
                "unexcused_absences": 2,
            },
        ],
        "achievements": [
            {
                "code": "ACH-01",
                "description": "Resuelve sistemas de ecuaciones lineales de primer grado.",
                "performance_level": "BASICO",
            }
        ],
    }
    save_ok_resp = await client.post(
        "/api/v1/evaluations/period-grades",
        headers={"Authorization": f"Bearer {f['teacher_assigned_token']}"},
        json=valid_save_payload,
    )
    assert save_ok_resp.status_code == 200, save_ok_resp.text
    assert save_ok_resp.json()["saved_count"] == 2


# ===========================================================================
# 3. Recovery / Remediation Grade Capping API Tests
# ===========================================================================


@pytest.mark.asyncio
async def test_recovery_grade_recording_and_cap_enforcement(
    client: AsyncClient,
    db_session: AsyncSession,
    siee_api_fixture: dict[str, Any],
) -> None:
    f = siee_api_fixture
    p_id = str(f["period"].id)
    g_id = str(f["group_9a"].id)
    s_id = str(f["subject_mat"].id)
    st2_id = str(f["student2"].id)
    enr2_id = str(f["enr2"].id)

    # First save failing grade for student 2 (score 2.0)
    save_payload = {
        "period_id": p_id,
        "group_id": g_id,
        "subject_id": s_id,
        "items": [
            {
                "student_id": st2_id,
                "enrollment_id": enr2_id,
                "calculated_score": 2.0,
                "final_score": 2.0,
                "adjustment_reason": None,
            }
        ],
    }
    await client.post(
        "/api/v1/evaluations/period-grades",
        headers={"Authorization": f"Bearer {f['teacher_assigned_token']}"},
        json=save_payload,
    )

    # Query the grade record from DB
    grade_stmt = select(PeriodSubjectGrade).where(
        PeriodSubjectGrade.student_id == f["student2"].id,
        PeriodSubjectGrade.subject_id == f["subject_mat"].id,
    )
    grade = (await db_session.execute(grade_stmt)).scalars().first()
    assert grade is not None

    # Record recovery grade with score 4.8 (should be capped at recovery_grade_cap = 3.0)
    recovery_payload = {
        "recovery_score": 4.80,
        "recovery_date": str(date(2026, 4, 20)),
        "act_number": "ACTA-REC-001",
        "observations": "Supero satisfactoriamente la prueba de nivelacion",
    }
    rec_resp = await client.post(
        f"/api/v1/evaluations/grades/{grade.id}/recoveries",
        headers={"Authorization": f"Bearer {f['teacher_assigned_token']}"},
        json=recovery_payload,
    )
    assert rec_resp.status_code == 201, rec_resp.text
    rec_data = rec_resp.json()
    assert rec_data["initial_score"] == 2.00
    assert rec_data["recovery_score"] == 4.80
    assert rec_data["applied_cap"] == 3.00
    assert rec_data["final_adjusted_score"] == 3.00


# ===========================================================================
# 4. Period Closure and Reopening Lifecycle Tests
# ===========================================================================


@pytest.mark.asyncio
async def test_period_close_and_unlock_lifecycle(
    client: AsyncClient,
    siee_api_fixture: dict[str, Any],
) -> None:
    f = siee_api_fixture
    p_id = str(f["period"].id)
    g_id = str(f["group_9a"].id)
    s_id = str(f["subject_mat"].id)
    st1_id = str(f["student1"].id)
    enr1_id = str(f["enr1"].id)

    # 1. Close period as Rector
    close_resp = await client.post(
        f"/api/v1/evaluations/periods/{p_id}/close",
        headers={"Authorization": f"Bearer {f['rector_token']}"},
    )
    assert close_resp.status_code == 200, close_resp.text
    assert close_resp.json()["is_closed"] is True

    # 2. Attempt to save grades on closed period -> 409 Conflict
    save_payload = {
        "period_id": p_id,
        "group_id": g_id,
        "subject_id": s_id,
        "items": [
            {
                "student_id": st1_id,
                "enrollment_id": enr1_id,
                "calculated_score": 4.0,
                "final_score": 4.0,
            }
        ],
    }
    save_resp = await client.post(
        "/api/v1/evaluations/period-grades",
        headers={"Authorization": f"Bearer {f['teacher_assigned_token']}"},
        json=save_payload,
    )
    assert save_resp.status_code == 409, save_resp.text

    # 3. Unlock period with justification as Rector
    unlock_payload = {
        "reason": "Reapertura autorizada por Consejo Directivo para asentar actas de nivelacion extemporaneas."
    }
    unlock_resp = await client.post(
        f"/api/v1/evaluations/periods/{p_id}/unlock",
        headers={"Authorization": f"Bearer {f['rector_token']}"},
        json=unlock_payload,
    )
    assert unlock_resp.status_code == 200, unlock_resp.text
    assert unlock_resp.json()["is_closed"] is False

    # 4. Now saving grades succeeds
    save_after_unlock = await client.post(
        "/api/v1/evaluations/period-grades",
        headers={"Authorization": f"Bearer {f['teacher_assigned_token']}"},
        json=save_payload,
    )
    assert save_after_unlock.status_code == 200, save_after_unlock.text


# ===========================================================================
# 5. Report Cards & Anti-IDOR Security Tests
# ===========================================================================


@pytest.mark.asyncio
async def test_student_and_group_report_cards_with_anti_idor(
    client: AsyncClient,
    siee_api_fixture: dict[str, Any],
) -> None:
    f = siee_api_fixture
    p_id = str(f["period"].id)
    g_id = str(f["group_9a"].id)
    s_id = str(f["subject_mat"].id)
    year_id = str(f["academic_year"].id)
    st1_id = str(f["student1"].id)
    st2_id = str(f["student2"].id)

    # Save grades for both students first
    await client.post(
        "/api/v1/evaluations/period-grades",
        headers={"Authorization": f"Bearer {f['rector_token']}"},
        json={
            "period_id": p_id,
            "group_id": g_id,
            "subject_id": s_id,
            "items": [
                {
                    "student_id": st1_id,
                    "enrollment_id": str(f["enr1"].id),
                    "calculated_score": 4.5,
                    "final_score": 4.5,
                },
                {
                    "student_id": st2_id,
                    "enrollment_id": str(f["enr2"].id),
                    "calculated_score": 3.5,
                    "final_score": 3.5,
                },
            ],
        },
    )

    # 1. Student 1 views own report card -> 200 OK
    resp_st1_own = await client.get(
        f"/api/v1/evaluations/report-cards/student/{st1_id}?period_id={p_id}",
        headers={"Authorization": f"Bearer {f['student1_token']}"},
    )
    assert resp_st1_own.status_code == 200, resp_st1_own.text
    card1 = resp_st1_own.json()
    assert card1["student"]["id"] == st1_id
    assert card1["summary"]["rank"] == 1

    # 2. Student 1 attempts to view Student 2 report card -> 403 Forbidden (Anti-IDOR)
    resp_st1_st2 = await client.get(
        f"/api/v1/evaluations/report-cards/student/{st2_id}?period_id={p_id}",
        headers={"Authorization": f"Bearer {f['student1_token']}"},
    )
    assert resp_st1_st2.status_code == 403, resp_st1_st2.text

    # 3. Guardian (linked to Student 1) views Student 1 card -> 200 OK
    resp_guard_st1 = await client.get(
        f"/api/v1/evaluations/report-cards/student/{st1_id}?period_id={p_id}",
        headers={"Authorization": f"Bearer {f['guardian_token']}"},
    )
    assert resp_guard_st1.status_code == 200, resp_guard_st1.text

    # 4. Guardian attempts to view unlinked Student 2 card -> 403 Forbidden (Anti-IDOR)
    resp_guard_st2 = await client.get(
        f"/api/v1/evaluations/report-cards/student/{st2_id}?period_id={p_id}",
        headers={"Authorization": f"Bearer {f['guardian_token']}"},
    )
    assert resp_guard_st2.status_code == 403, resp_guard_st2.text

    # 5. Rector views group matrix -> 200 OK
    resp_matrix = await client.get(
        f"/api/v1/evaluations/report-cards/group/{g_id}/matrix?period_id={p_id}",
        headers={"Authorization": f"Bearer {f['rector_token']}"},
    )
    assert resp_matrix.status_code == 200, resp_matrix.text
    matrix_data = resp_matrix.json()
    assert matrix_data["total_students"] == 2

    # 6. Student views year-end report card -> 200 OK
    resp_ye = await client.get(
        f"/api/v1/evaluations/report-cards/student/{st1_id}/year-end?academic_year_id={year_id}",
        headers={"Authorization": f"Bearer {f['student1_token']}"},
    )
    assert resp_ye.status_code == 200, resp_ye.text
    assert resp_ye.json()["summary"]["cumulative_average"] == 4.5


# ===========================================================================
# 6. Academic Promotions API Tests (Preview & Commit)
# ===========================================================================


@pytest.mark.asyncio
async def test_academic_promotions_preview_and_commit(
    client: AsyncClient,
    db_session: AsyncSession,
    siee_api_fixture: dict[str, Any],
) -> None:
    f = siee_api_fixture
    g_id = str(f["group_9a"].id)
    year_id = str(f["academic_year"].id)
    st1_id = str(f["student1"].id)
    st2_id = str(f["student2"].id)

    # 1. Calculate promotion preview
    prev_resp = await client.get(
        f"/api/v1/promotions/preview?group_id={g_id}&academic_year_id={year_id}",
        headers={"Authorization": f"Bearer {f['rector_token']}"},
    )
    assert prev_resp.status_code == 200, prev_resp.text
    prev_data = prev_resp.json()
    assert len(prev_data["candidates"]) == 2

    # 2. Commit promotion act with PROMOVIDO for Student 1 and NO_PROMOVIDO for Student 2
    commit_payload = {
        "group_id": g_id,
        "academic_year_id": year_id,
        "acta_number": "ACTA-PROM-2026-9A",
        "decision_date": str(date(2026, 11, 28)),
        "observations": "Sesion ordinaria de Comision de Evaluacion y Promocion",
        "decisions": [
            {
                "student_id": st1_id,
                "promotion_status": "PROMOVIDO",
                "observations": "Aprobado con honores",
                "decided_by_committee": True,
            },
            {
                "student_id": st2_id,
                "promotion_status": "NO_PROMOVIDO",
                "observations": "Repite grado",
                "decided_by_committee": True,
            },
        ],
    }
    commit_resp = await client.post(
        "/api/v1/promotions/commit",
        headers={"Authorization": f"Bearer {f['rector_token']}"},
        json=commit_payload,
    )
    assert commit_resp.status_code == 200, commit_resp.text
    commit_data = commit_resp.json()
    assert commit_data["committed_count"] == 2

    # Verify semantic invariant DECISION-16-04: PROMOVIDO keeps enrollment ACTIVE
    enr1_db = await db_session.get(Enrollment, f["enr1"].id)
    assert enr1_db is not None
    assert enr1_db.status == EnrollmentStatus.ACTIVE
